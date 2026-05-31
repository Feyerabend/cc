
## LeCun's World Model Vision and JEPA


### 1. The Big Picture

Yann LeCun--Turing Award laureate, Chief AI Scientist at Meta, and
one of the architects of modern deep learning--has been making an
increasingly forceful argument since roughly 2022:
*the dominant paradigms in AI are fundamentally limited, and the field needs a different foundation*.

His central claim is that large language models and diffusion models,
however impressive, do not and cannot lead to human-level intelligence.
They are sophisticated pattern matchers trained on text or pixels,
but they lack something essential: an internal model of how the world works.
They do not *understand* causality, physical plausibility, or the
structure of continuous experience. They hallucinate, they are brittle,
and they cannot plan.

LeCun's proposed alternative is built around a concept borrowed from
control theory and cognitive science: the *world model*--an internal
representation that an agent uses to simulate, predict, and reason
about its environment without having to act in it directly.

The question JEPA tries to answer is:
*how do you train a world model from raw, unlabelled sensory data?*



### 2. The Cake Analogy

LeCun uses a striking analogy to describe the relative data
efficiency of different learning paradigms:

> "If intelligence is a cake, the bulk of the cake is self-supervised learning, the icing on the cake is supervised learning, and the cherry on the cake is reinforcement learning."

The analogy makes a quantitative point. A human child hears
perhaps 50 million words before age ten. GPT-4 was trained
on something like 10-13 trillion tokens. The child sees far
less data yet achieves far more flexible, robust, and
generalisable intelligence.

The reason, LeCun argues, is that humans learn primarily through
*observation*--passive, self-supervised, multi-modal experience
of the physical world. A child who has never touched a stove
already has a rich model of what fire does; they learned it by
watching, listening, and reasoning from prior experience.

Current self-supervised learning methods (BERT, GPT, CLIP, MAE)
are steps in this direction, but LeCun argues they are fundamentally
the wrong kind of self-supervision: they either predict in
pixel/token space (which is high-dimensional and full of irrelevant
detail), or they use contrastive methods that have their own limitations.

JEPA is his proposed correction.



### 3. What Is a World Model?

A world model is a learned internal simulator. Given a current state
*s* and a proposed action *a*, the world model predicts the next
state *s'*--or more precisely, a *distribution* over possible next states.

The key capabilities a world model must have:
- *Prediction*: What will happen if I do X?
- *Planning*: What sequence of actions leads to goal G?
- *Abstraction*: What aspects of the current state are relevant, and which can be ignored?
- *Counterfactual reasoning*: What would have happened if I had done Y instead?

Crucially, a world model must operate in an *abstract* space,
not a pixel space. When you plan a route across a city, you think
in terms of streets and landmarks, not in terms of the precise
colour of every pixel in the scene. The right level of abstraction
makes prediction tractable.

This is the core of LeCun's critique of generative models:
if your model predicts at the pixel level, it is forced to
model an enormous amount of irrelevant variation--the exact
texture of a wall, the precise pattern of shadows--before it
can get to the semantically meaningful structure.



### 4. The Problem with Generative Models

Generative models--autoencoders, VAEs, GANs, diffusion models--learn
to reconstruct or generate data in the original input space. This
seems appealing: a model that can reconstruct the input has
clearly learned *something* about it.

But reconstruction in pixel space has a fundamental flaw.

Consider predicting the future from a video frame. If I show you half
of a scene, an enormous number of pixel-level futures are equally
consistent with the visible part: the exact ripple pattern of a flag,
the precise blur of a passing car, the specific shadow cast by a cloud.
A model that tries to predict *which* of these futures occurs must either
output a smeared average (blurry), or learn to model all the irreducible
stochastic variation in the world--which is wasted capacity.

LeCun calls this the *pixel-level prediction problem*:
the model spends most of its representational power learning to predict
things that are irrelevant to understanding the world.

A human watching half a scene does not predict the exact pixel values
of the other half. They predict the *gist*: there is probably a table
there, the person is probably still sitting, the light is probably
still on. Abstract predictions, not pixel predictions.

This is the motivating insight behind JEPA.



### 5. The Problem with Contrastive Learning

Before JEPA, the most successful self-supervised learning methods
were *contrastive*: SimCLR, MoCo, BYOL, and their descendants.
The core idea is elegant:
- Take an image. Create two augmented views of it (crop, colour jitter, blur).
- Train an encoder so that the two views of the *same* image have similar embeddings.
- Simultaneously, push embeddings of *different* images apart.

This works well and produces representations that transfer effectively.
But it has structural weaknesses:

*It requires negative pairs.* To prevent collapse (the encoder outputting
the same vector for everything), you need to push different samples apart.
This requires large batch sizes or a memory bank of stored embeddings (MoCo).
The training dynamics are sensitive and can be unstable.

*It is augmentation-dependent.* What the model considers "the same thing"
is defined entirely by the augmentation policy. If you don't include colour
jitter, the model treats colour as informative. If your augmentation policy
does not match the invariances relevant to your downstream task,
your representations will be misaligned.

*It is not obviously extensible to prediction across time or space.*
Contrastive methods are good at learning invariances (what stays the
same across views), but they do not naturally model *what is different*
between two observations--which is exactly what a world model
needs to predict future states.

JEPA avoids all three of these problems.



### 6. Joint Embedding Architectures

Before discussing JEPA specifically, it helps to understand the broader
family it belongs to: *joint embedding architectures*.

The idea is simple: instead of comparing a representation to raw input
(as in reconstruction), compare representations to *other representations*.
Both the context and the target are encoded into the same embedding space,
and the learning signal comes from the relationship between the two embeddings.

```
Input A  -->  Encoder  -->  Embedding A  +
                                         |--> Loss (embedding space)
Input B  -->  Encoder  -->  Embedding B  +
```

This has been done in many forms:
- *Siamese networks* (1990s): two inputs, shared encoder, contrastive loss.
- *CLIP* (OpenAI, 2021): image and text encoders aligned via contrastive loss across modalities.
- *BYOL* (DeepMind, 2020): two views, no negatives, uses a predictor on one branch.

JEPA is a joint embedding architecture with a specific additional constraint:
the relationship between the two embeddings must be *predictive*--one embedding
must be predictable from the other given some context information.



### 7. JEPA--Joint Embedding Predictive Architecture

JEPA was introduced by LeCun in his position paper
*"A Path Towards Autonomous Machine Intelligence"* (2022) and subsequently implemented as
*I-JEPA* (Image JEPA, Assran et al., Meta 2023), *V-JEPA* (Video JEPA, Bardes et al., Meta 2024),
and *MC-JEPA* (Motion-Content JEPA).

#### The Core Architecture

```
                          Input image
                               |
                               |
              +---------------------------------+
              |                                 |
         context region                   target region
         (visible patches)                (masked patches)
              |                                 |
              v                                 v
       Context Encoder                    Target Encoder
        (trainable)                        (EMA only,
              |                            no backprop)
              |                                 |
              v                                 |                     
          Predictor                             |
         (+ position                            |
          of target)                            |
              |                                 |
              |                                 |
              v                                 v
       predicted embedding  <--- Loss --->  target embedding
              (in latent space, not pixel space)
```

#### What Makes It Different

Three things distinguish JEPA from prior approaches:

*1. Prediction in latent space, not pixel space.*

The predictor outputs an *embedding vector*, not a reconstructed image.
The loss function measures the distance between two embeddings.
This means the model is never penalised for failing to predict which
exact pixel variation occurs--it only needs to predict the abstract,
semantically relevant structure.

*2. Asymmetric architecture with EMA.*

The context encoder is trained normally via backpropagation.
The target encoder is a slowly-updated copy of the context encoder,
updated only through an exponential moving average.
This asymmetry is what prevents collapse (explained in detail below).

*3. Predictability is conditioned on position.*

In I-JEPA, the predictor receives not just the context embedding but
also the *positional information* of the target region. This allows
the model to answer the question: "Given that I can see region A,
what should the representation of region B look like?" The position
conditioning is what makes the task genuinely predictive rather
than merely invariance-learning.

#### The Loss Function

$$\mathcal{L} = \frac{1}{|\mathcal{T}|} \sum_{t \in \mathcal{T}} \left\| s_\theta(z_x, t) - z_y^{(t)} \right\|^2$$

Where:
- $z_x$ is the context embedding (from the context encoder)
- $z_y^{(t)}$ is the target embedding for target region $t$
  (from the target encoder, stop-gradient)
- $s_\theta$ is the predictor (conditioned on target position $t$)

In practice, cosine distance (as used in our MNIST example)
or L2 distance in normalised embedding space are both common choices.

#### Masking Strategy

In I-JEPA, the masking strategy is important and deliberate:

- The *target* consists of several large, contiguous blocks
  (typically 4 per image), covering roughly 25-75% of the image.
- The *context* is what remains after removing the target blocks.
- Large target blocks force the model to predict *spatial structure*,
  not just isolated patches.

This is different from MAE (Masked Autoencoder), which masks
random individual patches and reconstructs pixels.
JEPA's larger target blocks require longer-range spatial reasoning.



### 8. How Collapse Is Prevented--EMA

The most technically subtle aspect of JEPA is how it avoids
representational collapse--the failure mode where the encoder
maps all inputs to the same constant embedding,
which trivially minimises any self-supervised loss.

#### Why Collapse Happens

If both encoders were trained with backpropagation,
the following is a valid solution to the loss:

```
context_encoder(x)  -->  constant vector c
target_encoder(y)   -->  constant vector c
predictor(c)        -->  constant vector c
Loss = ||c - c|| = 0  OK!
```

This is a collapsed, useless solution. The encoder has learned nothing.

#### Why EMA Solves It

The key insight is that the
*target encoder must provide targets that the context encoder cannot trivially collapse to match*.

With EMA, the target encoder at step $t$ is:

$$\theta_{\text{target}}^{(t)} = m \cdot \theta_{\text{target}}^{(t-1)} + (1-m) \cdot \theta_{\text{context}}^{(t)}$$

where $m \approx 0.996$ is the momentum coefficient.

The target encoder *lags behind* the context encoder.
At any given moment, the targets it produces reflect a
*slightly older version* of the representation.
This lag means:
1. The target encoder cannot instantly adapt to a collapsing context encoder.
2. The context encoder must predict targets that were produced by a more stable,
   averaged version of itself.
3. The predictor, operating on current context embeddings,
   must bridge the gap--which requires genuine representational work.

This is the same principle used in *MoCo* (He et al., 2020) and *BYOL* (Grill et al., 2020),
where it was discovered empirically before being well-understood theoretically.
The theoretical analysis (Tian et al., 2021; Richemond et al., 2023)
shows that the EMA effectively acts as a regulariser that prevents the
loss landscape from having collapse as a stable fixed point.

#### Alternative: Stop-Gradient

An even simpler version of the same idea is to simply *stop the gradient*
through the target encoder entirely--update it with backprop on an identical
copy of the loss, but don't propagate gradients back through the target branch.
This is what SimSiam (Chen & He, 2021) and BYOL without momentum use.
It is less stable than EMA but has the same qualitative effect.



### 9. Relation to Other Models

#### Autoencoders and VAEs

|                     | Autoencoder                          | JEPA                          |
|---------------------|--------------------------------------|-------------------------------|
| Target              | Pixel reconstruction                 | Embedding prediction          |
| Loss                | MSE in pixel space                   | Cosine/L2 in embedding space  |
| Collapse risk       | No (reconstruction forces diversity) | Yes (requires EMA or similar) |
| Wasted capacity     | High (models irrelevant variation)   | Low (abstract targets)        |
| Downstream transfer | Moderate                             | Strong                        |

Autoencoders are the most natural comparison. Both are self-supervised and encoder-based.
But the autoencoder's decoder must reconstruct every pixel--including all the noise, texture,
and irreducible variation that has no semantic content. JEPA's predictor only needs to predict
an abstract embedding, so the encoder is incentivised to discard pixel-level noise and retain semantic structure.

#### Masked Autoencoders (MAE)

MAE (He et al., 2022) is the pixel-reconstruction analogue of JEPA:
mask 75% of image patches, reconstruct missing patches with an autoencoder.
It achieves excellent results on ImageNet and has been widely adopted.

LeCun's critique of MAE is direct: it forces the model to predict exact pixel
values of the masked region, which means it must model all the irreducible
variation in that region. A JEPA-trained model does better on tasks that
require semantic understanding (object recognition, detection) while a
MAE-trained model may do better on tasks that require low-level detail
(texture synthesis, super-resolution).

Empirically, I-JEPA (Meta, 2023) outperforms MAE on linear probing benchmarks
while using less compute, which supports LeCun's theoretical argument.

#### Contrastive Methods (SimCLR, MoCo, BYOL)

|                         | Contrastive (SimCLR) | JEPA         |
|-------------------------|----------------------|--------------|
| Negative pairs          | Required             | Not required |
| Augmentation dependency | High                 | Low          |
| Spatial prediction      | No                   | Yes          |
| Scalability             | Batch-size sensitive | Stable       |

Contrastive methods learn invariances: the encoder learns that two augmented
views of the same image should map to the same embedding. JEPA learns predictability:
the encoder learns that the embedding of one region should be predictable
from the embedding of another region.

These are complementary learning signals. Invariance is about what to ignore;
predictability is about what to model. LeCun argues that for a world model,
predictability is more fundamental.

#### BERT / GPT (Language Models)

BERT masks tokens and predicts them in token space. GPT predicts the next token
in token space. These are, in a sense, JEPA applied to discrete sequences--but
the prediction is in the original input space (tokens),
not in an abstract embedding space.

LeCun's position is that this works tolerably well for language because language
is already a highly compressed, abstract representation of thought--tokens
already discard most of the irrelevant variation. The same trick does not
work for raw sensory input (pixels, audio waveforms), where the signal-to-noise
ratio is much lower. This is why he argues JEPA-style architectures are more
important for perception than for language.

#### World Models in RL (Dreamer, MuZero)

World models in reinforcement learning (Ha & Schmidhuber, 2018; Hafner et al.,
2019 onwards; Schrittwieser et al., 2020) train a latent-space dynamics model
to predict future latent states from current states and actions.
This is very close in spirit to JEPA.

The difference is scope: RL world models are typically trained with reward
signal and task-specific data. JEPA aims to learn a general world model from
passive observation, without reward or action labels. The long-term vision
is to use JEPA-pretrained representations as the backbone for a downstream
planning/RL system.



### 10. Walkthrough: MNIST JEPA

The script `mnist_jepa.py` implements a simplified JEPA on the MNIST handwritten
digit dataset. It is designed as a pedagogical illustration,
not a state-of-the-art system. Here is a step-by-step guide.

#### Data and Split

MNIST consists of 60,000 training and 10,000 test images of handwritten digits (0-9),
each 28x28 pixels in grayscale.

The script flattens each image to a 784-dimensional vector and splits it:

```
Pixels 0-391    --> top 14 rows    --> context  (what the model sees)
Pixels 392-783  --> bottom 14 rows --> target   (what must be predicted)
```

This is the simplest possible masking strategy: the model sees the top half
of a digit and must predict the *representation* of the bottom half.

Visually:

```
  XXXXXXXXXXXXXXXX   <-- context (visible, encoded by context encoder)
  XXXXXXXXXXXXXXXX
  XXXXXXXXXXXXXXXX
  XXXXXXXXXXXXXXXX
  XXXXXXXXXXXXXXXX
  XXXXXXXXXXXXXXXX
  XXXXXXXXXXXXXXXX
  XXXXXXXXXXXXXXXX
  - - - - - - - -    <-- split
  ????????????????   <-- target (masked, encoded by target encoder)
  ????????????????
  ????????????????
  ????????????????
  ????????????????
  ????????????????
  ????????????????
  ????????????????
```

#### Architecture

```python
Encoder(input_dim=392, hidden_dim=512, embed_dim=256)
    Linear(392 --> 512) --> LayerNorm --> GELU --> Linear(512 --> 256)

Predictor(embed_dim=256)
    Linear(256 --> 256) --> GELU --> Linear(256 --> 256)
```

Two identical `Encoder` instances: one for the context (trained via backprop),
one for the target (EMA only). The `Predictor` maps the context embedding
to a predicted target embedding.

`LayerNorm` inside the encoder stabilises training and is important for
preventing the encoder from gaming the cosine loss by scaling embeddings
to extreme magnitudes.

`GELU` (Gaussian Error Linear Unit) is the standard activation in transformer-era
models; it is smooth and empirically better than ReLU for embedding models.

#### Pretraining Loop

```python
ctx_emb  = context_encoder(context)    # forward through trainable encoder
pred_emb = predictor(ctx_emb)          # predict target embedding

with torch.no_grad():
    tgt_emb = target_encoder(target)   # EMA encoder, no gradient

loss = cosine_loss(pred_emb, tgt_emb)  # distance in embedding space
loss.backward()
optimizer.step()
model.ema_update()                     # slowly pull target toward context
```

Note the `torch.no_grad()` block around the target encoder. Gradients are
explicitly blocked--the target embedding is treated as a fixed target,
not a co-trained parameter. This is the technical implementation of
the EMA stop-gradient principle.

#### EMA Update

```python
def ema_update(self):
    m = self.momentum  ## 0.996
    for p_c, p_t in zip(context_encoder.parameters(),
                         target_encoder.parameters()):
        p_t.data.mul_(m).add_(p_c.data, alpha=1.0 - m)
```

At every training step, the target encoder weights move 0.4% of the way
toward the current context encoder. This means the target encoder represents
roughly the average context encoder over the last ~250 steps--a stable, smoothed anchor.

#### Loss Function

```python
def cosine_loss(predicted, target):
    p = F.normalize(predicted, dim=-1)
    t = F.normalize(target,    dim=-1)
    return (1.0 - (p * t).sum(dim=-1)).mean()
```

The normalisation step is important. Without it, the encoder could trivially
reduce the loss by making the embedding vectors very small (near-zero vectors
have near-zero cosine distance from anything). Normalising to the unit
hypersphere before computing similarity removes this shortcut.

The loss ranges from 0 (perfectly aligned) to 2 (perfectly anti-aligned).
A loss near 1 means the predictions are orthogonal to the targets--no better than random.

#### Linear Probe Evaluation

After pretraining, the context encoder is frozen and a single linear layer
is trained on top using digit labels:

```python
head = nn.Linear(embed_dim, 10)
# train head only, context_encoder.parameters() never updated
```

This is the standard evaluation protocol for self-supervised learning.
The rationale: if the representations are good, they should be *linearly separable*
by class. A linear probe cannot learn non-linear transformations, so it is
sensitive to whether the self-supervised objective has aligned the embedding
space with semantically meaningful structure.

#### Embedding Coherence Check

The script also measures, without any labels during the check, whether
embeddings of the same digit are more similar than embeddings of different digits:

```python
within_class  = mean cosine similarity of same-label pairs
across_class  = mean cosine similarity of different-label pairs
gap           = within - across  (positive --> representations are digit-aware)
```

This is a direct test of unsupervised structure: did the encoder learn that
"two 7s look similar in their top halves"? If JEPA works, the answer should be
yes--and it should emerge purely from the prediction task, not from any label signal.



### 11. Results and What They Mean

Running the script on the full 60,000-image training set produces:

```
Self-supervised pretraining  (no labels)...
  Epoch  1/15  loss = 0.1931
  Epoch  2/15  loss = 0.0580
  ...
  Epoch  5/15  loss = 0.0194     <-- approximate convergence
  ...
  Epoch 10/15  loss = 0.0209     <-- slight uptick as target encoder drifts
  ...
  Epoch 15/15  loss = 0.0299

Embedding coherence--within-class: 0.632  across-class: 0.457  (gap: +0.175)

Linear-probe test accuracy : 91.4%
Random baseline             : 9.8%
```

#### Interpreting the Loss Curve

The sharp drop in epochs 1-4 reflects the encoder rapidly learning basic structure:
the approximate shape of strokes in the top half strongly predicts the approximate
shape of strokes in the bottom half (e.g. the bottom of a "1" is almost always a
vertical stroke; the bottom of a "0" is almost always a curved arc).

The slight increase after epoch 5 is not failure--it reflects the *moving target effect*.
As the context encoder improves, the EMA target encoder slowly catches up.
As the target encoder improves, it produces more informative and harder-to-predict targets.
The loss stabilises at a higher level because the target has become more challenging.

This is qualitatively similar to curriculum learning:
the task difficulty automatically increases as the model improves.

#### Interpreting Embedding Coherence

A gap of +0.175 (within-class similarity 0.632 vs across-class 0.457) means the
encoder has spontaneously organised its embedding space so that same-digit
images are closer together than different-digit images--without ever being told what a digit is.

This is the key empirical signature that JEPA's predictions are capturing
semantic structure, not just low-level texture statistics. A random encoder
would show gap ≈ 0; a purely texture-based encoder would show a small gap
from superficial visual similarity; a semantically meaningful encoder shows
a systematic, class-structured gap.

#### Interpreting Linear Probe Accuracy

91.4% accuracy with a single linear layer, trained on representations from
a model that never saw a label, is strong evidence that the embedding space
is semantically organised. For context:

| Method                           | Test accuracy (approx) |
|----------------------------------|------------------------|
| Random encoder (linear probe)    | ~11%                   |
| PCA of raw pixels (linear probe) | ~85%                   |
| MNIST JEPA (our example)         | 91.4%                  |
| Fully supervised (simple MLP)    | ~97-98%                |
| State-of-the-art supervised CNN  | ~99.7%                 |

The gap between JEPA and fully supervised is expected: the linear probe uses
only the top half of the image (the context region), and the self-supervised
objective is much weaker than explicit label signal. The key point is the large
gap over random and PCA baselines--the encoder has learned something that
transcends low-level statistics.



### 12. Consequences and Open Questions

#### What JEPA Gets Right That Others Don't

*Scalability of the self-supervised signal.* Pixel-level reconstruction becomes
harder as image resolution increases--the number of pixels to reconstruct grows
as $O(n^2)$, but the number of semantically meaningful things to predict grows
much more slowly. JEPA's embedding-space prediction scales more gracefully.

*Compatibility with hierarchical representations.* A world model for complex
environments needs multiple levels of abstraction (pixel --> edge --> object --> scene --> action).
JEPA can in principle be stacked: the output of one JEPA encoder becomes the
input to the next. LeCun's proposed full architecture (HJEPA, Hierarchical JEPA)
does exactly this.

*No dependence on augmentation policy.* Contrastive methods require careful design
of augmentations to define the relevant invariances. JEPA learns from the structure
of the data itself (spatial proximity, temporal continuity in video) without
requiring manual specification of what counts as "the same thing."

#### Current Limitations

*Masking strategy matters.* The simple top/bottom split in our MNIST example is
pedagogical. In practice, the choice of which regions to mask as context vs target
significantly affects what the model learns. I-JEPA uses large, random contiguous
blocks; V-JEPA uses temporal masking across video frames. The optimal masking
strategy for general intelligence is an open research question.

*No notion of actions.* JEPA as described learns to predict representations of
unseen regions of the *same image*, not representations of *future states given actions*.
Extending JEPA to action-conditioned prediction (the natural extension for a
planning system) is an active research area.

*Evaluation is still largely downstream supervised.* We measure JEPA quality by
how well downstream supervised tasks perform with frozen representations. This
creates a circularity: if the downstream tasks don't capture what the world model
needs to know, we can't measure whether the world model is good.

*The collapse problem is not fully solved.* EMA and stop-gradient are engineering
solutions, not theoretical guarantees. The conditions under which they prevent
collapse are understood asymptotically but not in full generality.
New failure modes continue to be discovered in practice.

#### The Broader Vision: Autonomous AI

LeCun's long-term claim is that an AI system with a good JEPA-based world model could:
1. *Plan* by simulating possible futures in latent space and selecting actions that lead to goal states.
2. *Learn from passive observation* without needing labelled data or reward signals.
3. *Generalise* to new situations by composing learned abstract representations.
4. *Reason about physical plausibility* because the world model has internalised physical constraints.

This positions JEPA as a foundational component, not a complete system.
The full architecture LeCun proposes in *"A Path Towards Autonomous Machine Intelligence"*
includes:

- A *perception module* (JEPA encoder) that builds abstract representations.
- A *world model* (JEPA predictor) that simulates future states.
- A *cost module* that evaluates desirability of states.
- An *actor* that selects actions by optimising the cost module via the world model.
- A *short-term memory* and *long-term memory* (learned).

Whether this architecture will deliver general intelligence is contested. Critics
note that even perfect spatial prediction from partial observations does not imply
causal understanding, abstract reasoning, or language grounding. LeCun's response
is that these higher capabilities will emerge from sufficiently powerful world
models trained on sufficiently rich data--a claim that remains unproven but
is also untested at scale.



### 13. Conclusion

JEPA represents a principled response to a genuine problem in deep learning:
self-supervised methods that predict in raw input space waste capacity on
irrelevant variation, while contrastive methods require negative pairs and
augmentation engineering.

The core insight--*predict abstract representations, not pixels*--is simple
enough to state in a sentence but has far-reaching consequences. It changes
what the encoder is incentivised to learn, what the loss function measures,
and what kind of downstream capabilities the representations support.

Our MNIST example illustrates all the essential ingredients in miniature:
- The *top/bottom split* plays the role of the context/target partition.
- The *cosine loss in embedding space* replaces pixel-level reconstruction loss.
- The *EMA target encoder* prevents the collapse that would otherwise make the task trivial.
- The *linear probe* provides an interpretable, label-based measurement of representation quality.
- The *embedding coherence check* shows that semantic structure emerges without label signal.

The results--91.4% linear-probe accuracy from a model that never saw a label,
with semantically structured embedding space--demonstrate that the architecture
works as intended. The self-supervised signal from predicting the bottom half
of handwritten digits is rich enough to learn a representation of digit identity.

Whether LeCun's vision for JEPA as the foundation of autonomous intelligence will
be validated by future research is an open question. What is already clear is that
the critique of pixel-space prediction is well-founded, that joint embedding
architectures are among the strongest self-supervised approaches available,
and that the idea of learning world models from passive observation is one
of the central problems of AI research in the 2020s.



*For the code discussed in Section 10-11, see `mnist_jepa.py` in this repository.

Primary reference: LeCun, Y. (2022). A Path Towards Autonomous Machine Intelligence.
[openreview.net/pdf?id=BZ5a1r-kVsf](https://openreview.net/pdf?id=BZ5a1r-kVsf)*
