import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
from torchvision import transforms
from torch.utils.data import DataLoader
import numpy as np

# Model with BatchNorm
class SimpleNet(nn.Module):
    def __init__(self):  # Fixed: was **init**
        super().__init__()
        self.fc1 = nn.Linear(28*28, 256)
        self.bn1 = nn.BatchNorm1d(256)
        self.fc2 = nn.Linear(256, 10)
    
    def forward(self, x):
        x = x.view(-1, 28*28)
        x = self.bn1(F.relu(self.fc1(x)))
        return self.fc2(x)

# Entropy loss for test-time adaptation
def entropy_loss(logits):
    probs = F.softmax(logits, dim=1)
    log_probs = torch.log(probs + 1e-6)
    return -torch.mean(torch.sum(probs * log_probs, dim=1))

# Load clean MNIST
transform = transforms.ToTensor()
train_data = torchvision.datasets.MNIST(root='./data', train=True, download=True, transform=transform)
test_data_clean = torchvision.datasets.MNIST(root='./data', train=False, download=True, transform=transform)

# Create noisy test version to simulate domain shift
def add_noise(x):
    noise = torch.randn_like(x) * 0.3
    return torch.clamp(x + noise, 0, 1)

# Apply noise transformation
test_transform_noisy = transforms.Compose([
    transforms.ToTensor(),
    transforms.Lambda(add_noise)
])

# Better approach: create noisy dataset with proper transformation
test_data_noisy = torchvision.datasets.MNIST(root='./data', train=False, download=False, transform=test_transform_noisy)

train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
test_loader_clean = DataLoader(test_data_clean, batch_size=64, shuffle=False)
test_loader_noisy = DataLoader(test_data_noisy, batch_size=64, shuffle=False)

# Train model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SimpleNet().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

print("Training model...")
for epoch in range(2):  # keep short for demo
    model.train()
    for batch_idx, (x, y) in enumerate(train_loader):
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()
        
        if batch_idx % 200 == 0:
            print(f'Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}')

# Evaluate on clean and noisy test data
def eval_model(model, dataloader, desc=""):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            preds = model(x).argmax(dim=1)
            correct += (preds == y).sum().item()
            total += y.size(0)
    accuracy = correct / total
    print(f"Accuracy {desc}: {accuracy:.4f}")
    return accuracy

# Evaluate before adaptation
acc_clean = eval_model(model, test_loader_clean, "on clean test set")
acc_before = eval_model(model, test_loader_noisy, "on noisy test set (before TTA)")

# Test-Time Adaptation: Entropy Minimization
print("\nPerforming Test-Time Adaptation...")

# Create optimizer that only updates BatchNorm parameters
bn_params = []
for name, param in model.named_parameters():
    if 'bn' in name:
        bn_params.append(param)

tta_optimizer = torch.optim.Adam(bn_params, lr=1e-3)

model.train()  # Allow batchnorm to adapt
adaptation_losses = []

for batch_idx, (x, _) in enumerate(test_loader_noisy):  # Fixed: was for x, * in test*loader_noisy
    x = x.to(device)
    
    # Forward pass
    logits = model(x)
    loss = entropy_loss(logits)
    
    # Backward pass - only update BN parameters
    tta_optimizer.zero_grad()
    loss.backward()
    tta_optimizer.step()
    
    adaptation_losses.append(loss.item())
    
    if batch_idx % 50 == 0:
        print(f'TTA Batch {batch_idx}, Entropy Loss: {loss.item():.4f}')

# Evaluate again after adaptation
acc_after = eval_model(model, test_loader_noisy, "on noisy test set (after TTA)")

print(f"\nResults Summary:")
print(f"Clean test accuracy: {acc_clean:.4f}")
print(f"Noisy test accuracy (before TTA): {acc_before:.4f}")
print(f"Noisy test accuracy (after TTA): {acc_after:.4f}")
print(f"Improvement: {acc_after - acc_before:.4f}")

# Plot adaptation progress (optional)
try:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(adaptation_losses)
    plt.title('Entropy Loss During TTA')
    plt.xlabel('Batch')
    plt.ylabel('Loss')
    
    plt.subplot(1, 2, 2)
    plt.bar(['Clean', 'Noisy (Before)', 'Noisy (After)'], [acc_clean, acc_before, acc_after])
    plt.title('Accuracy Comparison')
    plt.ylabel('Accuracy')
    plt.ylim(0, 1)
    
    plt.tight_layout()
    plt.show()
except ImportError:
    print("Matplotlib not available for plotting")