"""
MNIST JEPA — LeCun's Joint Embedding Predictive Architecture

Core idea: instead of reconstructing pixels (like an autoencoder), predict
abstract *representations* of masked regions. This forces the model to learn
meaningful structure rather than low-level texture.

Split strategy:
    Context  = top 14 rows  (392 pixels) — what the model sees
    Target   = bottom 14 rows (392 pixels) — what it must predict

Training signal: cosine distance between
    predictor(context_embedding)  vs  target_encoder(target_pixels)

Collapse prevention: the target encoder is *never* trained with backprop —
it is updated only as an Exponential Moving Average (EMA) of the context
encoder. This gives stable, slowly-drifting targets that can't be trivially
matched by a collapsing encoder.

Evaluation: freeze the context encoder, train a single linear layer with
labels. Good self-supervised representations → decent linear-probe accuracy.
"""

import os
import struct
import torch
import torch.nn as nn

MNIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ch04x", "mnist")

# To download MNIST automatically instead of using local files, uncomment the
# block below (requires: pip install torchvision) and remove the load_images /
# load_labels calls in main().
#
# from torchvision.datasets import MNIST
# from torchvision import transforms
# _ds_train = MNIST(root="./data", train=True,  download=True, transform=transforms.ToTensor())
# _ds_test  = MNIST(root="./data", train=False, download=True, transform=transforms.ToTensor())
# tr_imgs = _ds_train.data.float().view(-1, 784) / 255.0
# tr_lbls = _ds_train.targets
# te_imgs = _ds_test.data.float().view(-1, 784)  / 255.0
# te_lbls = _ds_test.targets


# Data

def load_images(path):
    with open(path, "rb") as f:
        _, n, rows, cols = struct.unpack(">IIII", f.read(16))
        raw = bytearray(f.read())
    return torch.tensor(raw, dtype=torch.float32).view(n, rows * cols) / 255.0


def load_labels(path):
    with open(path, "rb") as f:
        _, n = struct.unpack(">II", f.read(8))
        raw = bytearray(f.read(n))
    return torch.tensor(raw, dtype=torch.long)


# Model components

class Encoder(nn.Module):
    def __init__(self, input_dim=392, hidden_dim=512, embed_dim=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, embed_dim),
        )

    def forward(self, x):
        return self.net(x)


class Predictor(nn.Module):
    """Maps context embedding → predicted target embedding."""
    def __init__(self, embed_dim=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.GELU(),
            nn.Linear(embed_dim, embed_dim),
        )

    def forward(self, x):
        return self.net(x)


# JEPA

class MNISTJepa:
    def __init__(self, embed_dim=256, ema_momentum=0.996):
        self.context_encoder = Encoder(embed_dim=embed_dim)
        self.target_encoder  = Encoder(embed_dim=embed_dim)
        self.predictor       = Predictor(embed_dim=embed_dim)
        self.momentum        = ema_momentum

        # Target encoder starts as exact copy, then only moves via EMA
        for p_c, p_t in zip(self.context_encoder.parameters(),
                             self.target_encoder.parameters()):
            p_t.data.copy_(p_c.data)
        for p in self.target_encoder.parameters():
            p.requires_grad_(False)

    def ema_update(self):
        """Slowly pull target encoder toward context encoder."""
        m = self.momentum
        for p_c, p_t in zip(self.context_encoder.parameters(),
                             self.target_encoder.parameters()):
            p_t.data.mul_(m).add_(p_c.data, alpha=1.0 - m)

    def learnable_params(self):
        return list(self.context_encoder.parameters()) + \
               list(self.predictor.parameters())

    def train(self):
        self.context_encoder.train()
        self.predictor.train()

    def eval(self):
        self.context_encoder.eval()
        self.target_encoder.eval()
        self.predictor.eval()


def cosine_loss(predicted, target):
    """1 - mean cosine similarity. Zero when perfectly aligned."""
    p = nn.functional.normalize(predicted, dim=-1)
    t = nn.functional.normalize(target,    dim=-1)
    return (1.0 - (p * t).sum(dim=-1)).mean()


# Pretraining

def pretrain(model, images, epochs=10, batch_size=256, lr=3e-4):
    optimizer = torch.optim.Adam(model.learnable_params(), lr=lr)
    n = len(images)
    model.train()

    for epoch in range(epochs):
        perm       = torch.randperm(n)
        epoch_loss = 0.0
        steps      = 0

        for start in range(0, n, batch_size):
            batch   = images[perm[start : start + batch_size]]
            context = batch[:, :392]   # top 14 rows
            target  = batch[:, 392:]   # bottom 14 rows

            ctx_emb  = model.context_encoder(context)
            pred_emb = model.predictor(ctx_emb)

            with torch.no_grad():
                tgt_emb = model.target_encoder(target)

            loss = cosine_loss(pred_emb, tgt_emb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            model.ema_update()

            epoch_loss += loss.item()
            steps      += 1

        print(f"  Epoch {epoch + 1:2d}/{epochs}  loss = {epoch_loss / steps:.4f}")


# Linear probe evaluation

def linear_probe(model, tr_imgs, tr_lbls, te_imgs, te_lbls,
                 epochs=20, batch_size=256, lr=1e-3):
    """
    Freeze the encoder, fit one linear layer with labels.
    Linear-probe accuracy is the standard measure for self-supervised
    representation quality: a good encoder makes classes linearly separable.
    """
    model.eval()
    with torch.no_grad():
        tr_emb = model.context_encoder(tr_imgs[:, :392])
        te_emb = model.context_encoder(te_imgs[:, :392])

    head      = nn.Linear(tr_emb.shape[1], 10)
    optimizer = torch.optim.Adam(head.parameters(), lr=lr)
    loss_fn   = nn.CrossEntropyLoss()
    n         = len(tr_emb)

    head.train()
    for epoch in range(epochs):
        perm    = torch.randperm(n)
        correct = 0
        for start in range(0, n, batch_size):
            idx     = perm[start : start + batch_size]
            logits  = head(tr_emb[idx])
            loss    = loss_fn(logits, tr_lbls[idx])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            correct += (logits.argmax(1) == tr_lbls[idx]).sum().item()
        if (epoch + 1) % 5 == 0:
            print(f"  Probe epoch {epoch + 1:2d}/{epochs}  "
                  f"train acc = {correct / n * 100:.1f}%")

    head.eval()
    with torch.no_grad():
        test_acc = (head(te_emb).argmax(1) == te_lbls).float().mean().item() * 100
    print(f"\n  Linear-probe test accuracy : {test_acc:.1f}%")
    return test_acc


# Embedding quality check

def embedding_coherence(model, images, labels, n_samples=2000):
    """
    Are same-class embeddings more similar than cross-class ones?
    Reports mean cosine similarity: within-class vs across-class.
    A well-trained encoder should show within > across.
    """
    model.eval()
    with torch.no_grad():
        emb = nn.functional.normalize(
            model.context_encoder(images[:n_samples, :392]), dim=-1
        )
    lbl = labels[:n_samples]

    # Sample 2000 random pairs
    torch.manual_seed(0)
    i = torch.randint(0, n_samples, (2000,))
    j = torch.randint(0, n_samples, (2000,))
    sim       = (emb[i] * emb[j]).sum(dim=-1)
    same_cls  = (lbl[i] == lbl[j])

    within  = sim[ same_cls].mean().item()
    across  = sim[~same_cls].mean().item()
    print(f"  Embedding coherence — within-class: {within:.3f}  "
          f"across-class: {across:.3f}  "
          f"(gap: {within - across:+.3f})")


# Main

def main():
    print("MNIST JEPA — LeCun's Joint Embedding Predictive Architecture")
    print("=" * 60)

    print("\nLoading MNIST...")
    tr_imgs = load_images(os.path.join(MNIST_DIR, "train-images.idx3-ubyte"))
    tr_lbls = load_labels(os.path.join(MNIST_DIR, "train-labels.idx1-ubyte"))
    te_imgs = load_images(os.path.join(MNIST_DIR, "t10k-images.idx3-ubyte"))
    te_lbls = load_labels(os.path.join(MNIST_DIR, "t10k-labels.idx1-ubyte"))
    print(f"  {len(tr_imgs):,} train  /  {len(te_imgs):,} test")

    print("\nArchitecture:")
    print("  Context  encoder  →  Predictor  →  predicted embedding")
    print("  Target   encoder (EMA only, ∇ = 0)  →  target embedding")
    print("  Loss: cosine distance  (prediction vs target, in latent space)")
    print("  Split: top 14 rows = context,  bottom 14 rows = target")

    model = MNISTJepa(embed_dim=256, ema_momentum=0.996)

    print("\nSelf-supervised pretraining  (no labels)...")
    pretrain(model, tr_imgs, epochs=15, batch_size=256, lr=3e-4)

    print("\nEmbedding coherence before linear probe:")
    embedding_coherence(model, tr_imgs, tr_lbls)

    print("\nLinear probe  (encoder frozen, one layer trained with labels)...")
    linear_probe(model, tr_imgs, tr_lbls, te_imgs, te_lbls, epochs=20)

    rand_acc = (torch.randint(0, 10, te_lbls.shape) == te_lbls).float().mean().item() * 100
    print(f"  Random baseline             : {rand_acc:.1f}%")

    print("\nWhat LeCun's JEPA demonstrates on MNIST:")
    print("  1. No label is ever used during pretraining.")
    print("  2. The encoder learns by predicting abstract embeddings,")
    print("     not by reconstructing pixels — avoids wasted capacity.")
    print("  3. EMA on the target encoder prevents representation collapse")
    print("     without needing negative pairs (unlike contrastive methods).")
    print("  4. The linear probe shows the representations are digit-aware")
    print("     even though the model never saw a digit label.")


if __name__ == "__main__":
    main()
