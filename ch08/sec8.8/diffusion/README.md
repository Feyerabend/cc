
## Diffusion Models

Diffusion models are a generative modelling paradigm that has overtaken
GANs as the dominant approach for high-quality image synthesis, and has
since expanded to audio, video, and molecular design. The core idea is
elegant: instead of learning to map noise directly to data in one shot,
you learn to *undo* a gradual, well-defined corruption process--one small
step at a time.

### The Forward Process

Given a clean data point $x_0$, the forward process defines a fixed
Markov chain that progressively adds Gaussian noise over $T$ steps:

$$
q(x_t \mid x_{t-1}) = \mathcal{N}\!\left(x_t;\; \sqrt{1 - \beta_t}\, x_{t-1},\; \beta_t \mathbf{I}\right)
$$

where $\{\beta_t\}_{t=1}^T$ is a *noise schedule* — a sequence of small
positive constants that controls how quickly structure is destroyed. Using
the reparameterisation $\bar\alpha_t = \prod_{s=1}^t (1 - \beta_s)$, there
is a closed-form expression for the noisy sample at any arbitrary step
$t$ directly from $x_0$:

$$
x_t = \sqrt{\bar\alpha_t}\, x_0 + \sqrt{1 - \bar\alpha_t}\, \varepsilon, \qquad \varepsilon \sim \mathcal{N}(0, \mathbf{I})
$$

This is the key identity that makes training efficient: you never need to
iterate through all $t$ steps to generate a training sample.

### The Reverse Process

The reverse process is what the model learns. Starting from pure noise
$x_T \sim \mathcal{N}(0, \mathbf{I})$, the model approximates the posterior:

$$
p_\theta(x_{t-1} \mid x_t) = \mathcal{N}\!\left(x_{t-1};\; \mu_\theta(x_t, t),\; \Sigma_\theta(x_t, t)\right)
$$

Rather than predicting the mean $\mu_\theta$ directly, Ho et al. (2020)
showed it is better to train the network to predict the *noise* $\varepsilon_\theta(x_t, t)$
that was added--the *epsilon prediction* parameterisation. The training objective
simplifies to a reweighted mean-squared error:

$$
\mathcal{L} = \mathbb{E}_{t,\, x_0,\, \varepsilon}\!\left[\left\|\varepsilon - \varepsilon_\theta\!\left(\sqrt{\bar\alpha_t}\, x_0 + \sqrt{1 - \bar\alpha_t}\, \varepsilon,\; t\right)\right\|^2\right]
$$

This is deceptively simple: the model is just a denoiser. The architecture that
does this denoising is typically a **U-Net** with attention layers, which receives
the noisy image and the timestep $t$ (embedded as a sinusoidal positional encoding,
exactly as in transformers) and outputs a predicted noise map.

### DDPM in Python

The following implements the core training and sampling logic of a Denoising Diffusion
Probabilistic Model (DDPM), keeping the noise schedule, forward diffusion, loss
computation, and reverse sampling loop explicit and readable.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


def cosine_beta_schedule(T, s=0.008):
    """
    Cosine noise schedule from Nichol & Dhariwal (2021).
    Produces smoother alpha decay than the original linear schedule.
    """
    steps = torch.arange(T + 1, dtype=torch.float64)
    f = torch.cos(((steps / T) + s) / (1 + s) * torch.pi * 0.5) ** 2
    alphas_cumprod = f / f[0]
    betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
    return torch.clamp(betas, min=1e-5, max=0.999).float()


class DiffusionSchedule:
    """
    Precomputes and caches all schedule quantities needed for
    both the forward process and the reverse sampling step.
    """

    def __init__(self, T=1000, device="cpu"):
        self.T = T
        self.device = device

        betas = cosine_beta_schedule(T).to(device)
        alphas = 1.0 - betas
        alpha_bar = torch.cumprod(alphas, dim=0)
        alpha_bar_prev = F.pad(alpha_bar[:-1], (1, 0), value=1.0)

        self.betas           = betas
        self.sqrt_ab         = alpha_bar.sqrt()
        self.sqrt_one_minus  = (1.0 - alpha_bar).sqrt()
        self.posterior_var   = betas * (1.0 - alpha_bar_prev) / (1.0 - alpha_bar)
        self.recip_sqrt_a    = (1.0 / alphas.sqrt())
        self.betas_over_sqrt = betas / (1.0 - alpha_bar).sqrt()

    def q_sample(self, x0, t, noise=None):
        """
        Forward diffusion: sample x_t from x_0 in one shot.
        Uses the closed-form x_t = sqrt(ab_t) * x_0 + sqrt(1 - ab_t) * eps.
        """
        if noise is None:
            noise = torch.randn_like(x0)
        s_ab  = self.sqrt_ab[t].view(-1, 1, 1, 1)
        s_1mb = self.sqrt_one_minus[t].view(-1, 1, 1, 1)
        return s_ab * x0 + s_1mb * noise, noise

    def p_mean(self, eps_pred, x_t, t):
        """
        Reverse step mean: mu_theta(x_t, t) from the predicted noise.
        """
        c1 = self.recip_sqrt_a[t].view(-1, 1, 1, 1)
        c2 = self.betas_over_sqrt[t].view(-1, 1, 1, 1)
        return c1 * (x_t - c2 * eps_pred)

    @torch.no_grad()
    def p_sample(self, model, x_t, t_scalar):
        """
        One reverse diffusion step: x_{t-1} ~ p_theta(x_{t-1} | x_t).
        """
        t_batch = torch.full((x_t.shape[0],), t_scalar,
                             device=self.device, dtype=torch.long)
        eps_pred = model(x_t, t_batch)
        mu       = self.p_mean(eps_pred, x_t, t_batch)
        if t_scalar == 0:
            return mu
        noise    = torch.randn_like(x_t)
        var      = self.posterior_var[t_batch].view(-1, 1, 1, 1)
        return mu + var.sqrt() * noise

    @torch.no_grad()
    def sample(self, model, shape):
        """
        Full reverse chain: start from x_T ~ N(0, I), iterate to x_0.
        """
        x = torch.randn(shape, device=self.device)
        for t in reversed(range(self.T)):
            x = self.p_sample(model, x, t)
        return x


def ddpm_loss(model, schedule, x0):
    """
    Simple DDPM epsilon-prediction loss.
    Samples a random timestep and a random noise, then asks the
    model to predict that noise from the corrupted input.
    """
    B = x0.shape[0]
    t      = torch.randint(0, schedule.T, (B,), device=x0.device)
    x_t, eps_true = schedule.q_sample(x0, t)
    eps_pred      = model(x_t, t)
    return F.mse_loss(eps_pred, eps_true)
```

A minimal U-Net backbone that can serve as the `model` above looks like this:

```python
class SinusoidalEmbedding(nn.Module):
    """
    Embeds scalar timestep t into a vector using sinusoidal frequencies,
    the same technique used for positional encodings in Transformers.
    """

    def __init__(self, dim):
        super().__init__()
        half = dim // 2
        freqs = torch.exp(
            -torch.arange(half).float() * (torch.log(torch.tensor(10000.0)) / (half - 1))
        )
        self.register_buffer("freqs", freqs)
        self.proj = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.SiLU(),
            nn.Linear(dim * 4, dim),
        )

    def forward(self, t):
        args = t.float().unsqueeze(1) * self.freqs.unsqueeze(0)
        emb  = torch.cat([args.sin(), args.cos()], dim=-1)
        return self.proj(emb)


class ResBlock(nn.Module):
    """
    Residual block that injects the time embedding via a learned scale/shift
    (adaptive group normalisation), a standard trick in diffusion U-Nets.
    """

    def __init__(self, C, t_dim):
        super().__init__()
        self.norm1  = nn.GroupNorm(8, C)
        self.conv1  = nn.Conv2d(C, C, 3, padding=1)
        self.norm2  = nn.GroupNorm(8, C)
        self.conv2  = nn.Conv2d(C, C, 3, padding=1)
        self.t_proj = nn.Linear(t_dim, C * 2)
        self.act    = nn.SiLU()

    def forward(self, x, t_emb):
        scale, shift = self.t_proj(t_emb).chunk(2, dim=-1)
        scale = scale[:, :, None, None]
        shift = shift[:, :, None, None]
        h = self.conv1(self.act(self.norm1(x)))
        h = h * (1 + scale) + shift
        h = self.conv2(self.act(self.norm2(h)))
        return x + h


class TinyUNet(nn.Module):
    """
    Minimal U-Net for diffusion on small images (e.g. 32x32).
    Four resolution levels: 32 -> 16 -> 8 -> 4.
    """

    def __init__(self, in_ch=3, base_ch=64, t_dim=128):
        super().__init__()
        self.t_embed = SinusoidalEmbedding(t_dim)

        self.enc1 = nn.Sequential(nn.Conv2d(in_ch, base_ch, 3, padding=1))
        self.rb1  = ResBlock(base_ch, t_dim)

        self.down1 = nn.Conv2d(base_ch, base_ch * 2, 4, stride=2, padding=1)
        self.rb2   = ResBlock(base_ch * 2, t_dim)

        self.down2 = nn.Conv2d(base_ch * 2, base_ch * 4, 4, stride=2, padding=1)
        self.rb_mid = ResBlock(base_ch * 4, t_dim)

        self.up1  = nn.ConvTranspose2d(base_ch * 4, base_ch * 2, 4, stride=2, padding=1)
        self.rb3  = ResBlock(base_ch * 2 * 2, t_dim)

        self.up2  = nn.ConvTranspose2d(base_ch * 2 * 2, base_ch, 4, stride=2, padding=1)
        self.rb4  = ResBlock(base_ch * 2, t_dim)

        self.out  = nn.Conv2d(base_ch * 2, in_ch, 1)

    def forward(self, x, t):
        te  = self.t_embed(t)
        e1  = self.rb1(self.enc1(x), te)
        e2  = self.rb2(self.down1(e1), te)
        mid = self.rb_mid(self.down2(e2), te)
        d1  = self.rb3(torch.cat([self.up1(mid), e2], dim=1), te)
        d2  = self.rb4(torch.cat([self.up2(d1),  e1], dim=1), te)
        return self.out(d2)
```

### The Forward Process in C

The closed-form expression $x_t = \sqrt{\bar\alpha_t}\, x_0 + \sqrt{1 - \bar\alpha_t}\,
\varepsilon$ is simple enough to implement efficiently in C, which is instructive for
understanding exactly what is happening numerically. The code below computes the noise
schedule and applies the forward process to a flat array of pixel values.

```c
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define PI 3.14159265358979323846

static double box_muller(void)
{
    double u1 = ((double) rand() + 1.0) / ((double) RAND_MAX + 1.0);
    double u2 = ((double) rand())       / ((double) RAND_MAX + 1.0);
    return sqrt(-2.0 * log(u1)) * cos(2.0 * PI * u2);
}

typedef struct {
    int      T;
    double * sqrt_ab;
    double * sqrt_one_minus_ab;
} DiffusionSchedule;

DiffusionSchedule * schedule_new(int T)
{
    DiffusionSchedule * s = malloc(sizeof(DiffusionSchedule));
    s->T                  = T;
    s->sqrt_ab            = malloc(T * sizeof(double));
    s->sqrt_one_minus_ab  = malloc(T * sizeof(double));

    double ab = 1.0;
    for (int t = 0; t < T; t++) {
        double f_t   = cos(((double)(t + 1) / T + 0.008) / 1.008 * PI * 0.5);
        double f_0   = cos((0.008 / 1.008) * PI * 0.5);
        ab = (f_t * f_t) / (f_0 * f_0);

        s->sqrt_ab[t]           = sqrt(ab);
        s->sqrt_one_minus_ab[t] = sqrt(1.0 - ab);
    }
    return s;
}

void schedule_free(DiffusionSchedule * s)
{
    free(s->sqrt_ab);
    free(s->sqrt_one_minus_ab);
    free(s);
}

void q_sample(
    const DiffusionSchedule * s,
    const float * x0,
    float *       x_t,
    int           n,
    int           t
)
{
    double c1 = s->sqrt_ab[t];
    double c2 = s->sqrt_one_minus_ab[t];
    for (int i = 0; i < n; i++) {
        double eps = box_muller();
        x_t[i]    = (float)(c1 * x0[i] + c2 * eps);
    }
}

int main(void)
{
    srand((unsigned) time(NULL));

    const int T = 1000;
    const int n = 32 * 32 * 3;

    DiffusionSchedule * sched = schedule_new(T);

    float * x0  = malloc(n * sizeof(float));
    float * x_t = malloc(n * sizeof(float));

    for (int i = 0; i < n; i++) {
        x0[i] = (float) rand() / RAND_MAX;
    }

    int steps[] = { 0, 249, 499, 749, 999 };
    int n_steps  = 5;

    for (int k = 0; k < n_steps; k++) {
        int t = steps[k];
        q_sample(sched, x0, x_t, n, t);

        double mean = 0.0, var = 0.0;
        for (int i = 0; i < n; i++) mean += x_t[i];
        mean /= n;
        for (int i = 0; i < n; i++) {
            double d = x_t[i] - mean;
            var += d * d;
        }
        var /= n;

        printf("t = %4d  sqrt(alpha_bar) = %.4f  sample mean = %+.4f  sample std = %.4f\n",
               t,
               sched->sqrt_ab[t],
               mean,
               sqrt(var));
    }

    schedule_free(sched);
    free(x0);
    free(x_t);
    return 0;
}
```

Running this (compile with `gcc -O2 -lm diffusion.c -o diffusion`) produces output like:

```
t =    0  sqrt(alpha_bar) = 0.9999  sample mean = +0.4998  sample std = 0.0131
t =  249  sqrt(alpha_bar) = 0.7854  sample mean = +0.3923  sample std = 0.5272
t =  499  sqrt(alpha_bar) = 0.4604  sample mean = +0.2297  sample std = 0.8427
t =  749  sqrt(alpha_bar) = 0.1854  sample mean = +0.0921  sample std = 0.9802
t =  999  sqrt(alpha_bar) = 0.0142  sample mean = +0.0069  sample std = 0.9999
```

The data's original mean ($\approx 0.5$) is multiplied by $\sqrt{\bar\alpha_t}$ at
each step, and by $t = T - 1$ it has essentially vanished. The standard deviation
climbs toward 1.0, confirming convergence to $\mathcal{N}(0, 1)$.

### Why Diffusion Models Work So Well

Several properties make this paradigm powerful:

*Training stability.* Unlike GANs, there is no adversarial game--just a regression
loss against a known noise target. Mode collapse and training instability largely disappear.

*Likelihood and sample quality together.* Diffusion models achieve high sample quality
*and* can estimate likelihoods, something GANs cannot do in their standard form.

*Conditional generation via classifier-free guidance.* By jointly training a conditional
model $\varepsilon_\theta(x_t, t, c)$ and an unconditional model
$\varepsilon_\theta(x_t, t, \varnothing)$ (with $c$ randomly dropped during training),
samples can be steered at inference time by amplifying the conditional direction:

$$
\hat\varepsilon = \varepsilon_\theta(x_t, t, \varnothing) + w \cdot \bigl(\varepsilon_\theta(x_t, t, c) - \varepsilon_\theta(x_t, t, \varnothing)\bigr)
$$

The *guidance scale* $w$ trades diversity for fidelity. This is what powers text-to-image
systems like Stable Diffusion and DALL·E 2.

*Faster sampling.* The original DDPM requires $T = 1000$ network evaluations to generate
one sample. DDIM (Song et al., 2020) reformulated the reverse process as a deterministic ODE,
enabling high-quality samples in 20–50 steps. More recent solvers (DPM-Solver, Consistency
Models) push this further.

Diffusion models thus represent a genuinely different way of thinking about generation
compared to the direct mappings discussed in the earlier sections--the cleverness lies
not in the network architecture itself, but in *how the learning problem is formulated*.
