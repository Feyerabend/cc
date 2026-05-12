import torch
import torch.nn as nn
import torch.nn.functional as F
import random
import numpy as np
import copy
from collections import defaultdict
from typing import Tuple, List, Optional

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)
random.seed(42)

# Corruption patterns - these are the "noisy" versions
corruption_patterns = {
    'the': ['teh', 'hte', 'th'],
    'cat': ['kat', 'cta', 'ct'],
    'sits': ['sitz', 'sitts', 'sits'],
    'dog': ['doge', 'dogge', 'dig'],
    'runs': ['runz', 'ruuns', 'rns'],
    'mat': ['mAt', 'matt', 'mt'],
    'fast': ['fasT', 'fst', 'fase'],
    'big': ['bigg', 'bg', 'bgi'],
    'small': ['smal', 'smll', 'samll']
}

# Create expanded vocabulary that includes ALL corrupted variants
base_vocab = ['<pad>', '<unk>', '<start>', '<end>', 'the', 'cat', 'sits', 'on', 'mat', '.', 
              'a', 'dog', 'runs', 'fast', 'big', 'small', 'red', 'blue', 'green']

# Add all corrupted variants to vocabulary
expanded_vocab = base_vocab.copy()
for clean_word, corruptions in corruption_patterns.items():
    for corrupt_word in corruptions:
        if corrupt_word not in expanded_vocab:
            expanded_vocab.append(corrupt_word)

vocab = expanded_vocab
word2idx = {w: i for i, w in enumerate(vocab)}
idx2word = {i: w for w, i in word2idx.items()}

print(f"Expanded vocabulary size: {len(vocab)}")

# Reverse mapping for correction
correction_map = {}
for clean_word, corrupted_versions in corruption_patterns.items():
    for corrupted in corrupted_versions:
        correction_map[corrupted] = clean_word

def encode(tokens):
    return torch.tensor([word2idx.get(t, word2idx['<unk>']) for t in tokens])

def decode(tensor):
    return [idx2word[i.item()] for i in tensor]

# .. with some probability
def corrupt_word(word, corruption_prob=0.3):
    if random.random() < corruption_prob and word in corruption_patterns:
        return random.choice(corruption_patterns[word])
    return word

# .. if possible
def correct_word(word):
    return correction_map.get(word, word)

class CorrectionAwareTransformer(nn.Module):
    def __init__(self, vocab_size, d_model=128, nhead=8, num_layers=4, dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.vocab_size = vocab_size
        
        # Embeddings
        self.emb = nn.Embedding(vocab_size, d_model)
        self.pos_enc = nn.Parameter(torch.randn(100, d_model) * 0.02)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead, 
            dim_feedforward=4*d_model,
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # Output heads
        self.ln_final = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size)  # next token prediction
        self.confidence_head = nn.Linear(d_model, 1)  # confidence in current token
        
        self.dropout = nn.Dropout(dropout)
        self.apply(self._init_weights)
        
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
        
    def forward(self, x):
        seq_len = x.size(1)
        pos_emb = self.pos_enc[:seq_len].unsqueeze(0).expand(x.size(0), -1, -1)
        
        # Embedding with positional encoding
        x = self.emb(x) + pos_emb
        x = self.dropout(x)
        
        # Transformer
        x = self.transformer(x)
        x = self.ln_final(x)
        
        # Outputs
        lm_logits = self.lm_head(x)
        confidence_logits = self.confidence_head(x)
        
        return lm_logits, confidence_logits


# TTA (Test-Time Adaptation) Components
class TTALoss(nn.Module):
    def __init__(self, entropy_weight=1.0, confidence_weight=0.5, consistency_weight=0.3):
        super().__init__()
        self.entropy_weight = entropy_weight
        self.confidence_weight = confidence_weight
        self.consistency_weight = consistency_weight
    
    def entropy_loss(self, logits: torch.Tensor) -> torch.Tensor:
        probs = F.softmax(logits, dim=-1)
        log_probs = F.log_softmax(logits, dim=-1)
        entropy = -(probs * log_probs).sum(dim=-1)
        return entropy.mean()
    
    def confidence_loss(self, confidence_logits: torch.Tensor, target_conf: float = 0.8) -> torch.Tensor:
        confidence = torch.sigmoid(confidence_logits)
        target = torch.full_like(confidence, target_conf)
        return F.mse_loss(confidence, target)
    
    def consistency_loss(self, logits1: torch.Tensor, logits2: torch.Tensor) -> torch.Tensor:
        probs1 = F.softmax(logits1, dim=-1)
        probs2 = F.softmax(logits2, dim=-1)
        return F.kl_div(F.log_softmax(logits1, dim=-1), probs2, reduction='batchmean')
    
    def forward(self, logits: torch.Tensor, confidence_logits: torch.Tensor, 
                logits_aug: Optional[torch.Tensor] = None) -> torch.Tensor:
        loss = 0.0
        
        # Entropy minimization
        if self.entropy_weight > 0:
            ent_loss = self.entropy_loss(logits)
            loss += self.entropy_weight * ent_loss
        
        # Confidence maximization
        if self.confidence_weight > 0:
            conf_loss = self.confidence_loss(confidence_logits)
            loss += self.confidence_weight * conf_loss
        
        # Consistency regularization (if augmented logits provided)
        if logits_aug is not None and self.consistency_weight > 0:
            cons_loss = self.consistency_loss(logits, logits_aug)
            loss += self.consistency_weight * cons_loss
        
        return loss

def create_input_augmentations(input_tokens: torch.Tensor, num_augs: int = 2) -> List[torch.Tensor]:
    augmentations = []
    
    for _ in range(num_augs):
        aug_tokens = input_tokens.clone()
        batch_size, seq_len = aug_tokens.shape
        
        for b in range(batch_size):
            for s in range(seq_len):

                # Small chance to introduce/modify corruption
                if torch.rand(1) < 0.1:  # 10% chance
                    current_token = idx2word[aug_tokens[b, s].item()]
                    
                    # If it's a word that can be corrupted
                    if current_token in corruption_patterns:
                        corrupted_options = corruption_patterns[current_token]
                        new_token = torch.randint(0, len(corrupted_options), (1,)).item()
                        corrupted_word = corrupted_options[new_token]
                        if corrupted_word in word2idx:
                            aug_tokens[b, s] = word2idx[corrupted_word]
        
        augmentations.append(aug_tokens)
    
    return augmentations

def adapt_at_test_time_enhanced(
    model: nn.Module,
    corrupted_input: torch.Tensor,
    steps: int = 10,
    lr: float = 1e-4,
    adaptation_mode: str = "partial"  # "full", "partial", "bn_only"
) -> nn.Module:
    # corruption-aware transformer

    # Clone model for adaptation (preserve original)
    adapted_model = copy.deepcopy(model)
    adapted_model.train()  # Enable training mode for adaptation
    
    # Configure which parameters to adapt
    if adaptation_mode == "full":
        # Adapt all parameters
        params_to_adapt = adapted_model.parameters()
    elif adaptation_mode == "partial":
        # Adapt only final layers (last transformer layer + heads)
        params_to_adapt = list(adapted_model.ln_final.parameters()) + \
                          list(adapted_model.lm_head.parameters()) + \
                          list(adapted_model.confidence_head.parameters())
    elif adaptation_mode == "bn_only":
        # Adapt only normalization layers
        params_to_adapt = []
        for module in adapted_model.modules():
            if isinstance(module, nn.LayerNorm):
                params_to_adapt.extend(module.parameters())
    else:
        raise ValueError(f"Unknown adaptation_mode: {adaptation_mode}")
    
    # Setup optimizer
    optimizer = torch.optim.AdamW(params_to_adapt, lr=lr, weight_decay=1e-5)
    
    # TTA loss function
    tta_loss_fn = TTALoss(entropy_weight=1.0, confidence_weight=0.5, consistency_weight=0.3)
    
    print(f"Starting TTA with {steps} steps, mode: {adaptation_mode}")
    
    for step in range(steps):
        optimizer.zero_grad()
        
        # Forward pass on original input
        logits, confidence_logits = adapted_model(corrupted_input)
        
        # Create augmented inputs for consistency (optional)
        augmented_inputs = create_input_augmentations(corrupted_input, num_augs=1)
        logits_aug = None
        if augmented_inputs:
            logits_aug, _ = adapted_model(augmented_inputs[0])
        
        # Compute TTA loss
        tta_loss = tta_loss_fn(logits, confidence_logits, logits_aug)
        
        # Backward pass
        tta_loss.backward()
        
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(params_to_adapt, max_norm=1.0)
        
        optimizer.step()
        
        # Log progress
        if step % max(1, steps // 3) == 0:
            avg_confidence = torch.sigmoid(confidence_logits).mean().item()
            print(f"  Step {step:2d}: Loss={tta_loss.item():.4f}, Confidence={avg_confidence:.3f}")
    
    adapted_model.eval()  # Set back to eval mode
    return adapted_model


# Generate text while being aware of input corruption and potentially correcting
def generate_with_correction(model, input_sequence, max_length=10, temperature=0.8, 
                           correction_threshold=0.5, use_tta=False, tta_steps=5):
    device = next(model.parameters()).device
    original_model = model
    
    # Pre-process input: correct low-confidence tokens
    corrected_sequence = input_sequence.copy()
    
    # Add start token if not present
    if corrected_sequence[0] != '<start>':
        corrected_sequence = ['<start>'] + corrected_sequence
    
    # Convert to tensor
    input_tokens = encode(corrected_sequence).unsqueeze(0).to(device)
    
    # OPTION 1: Use Test-Time Adaptation
    if use_tta:
        print(f"Applying TTA to input: {input_sequence}")
        model = adapt_at_test_time_enhanced(
            original_model, input_tokens, steps=tta_steps, lr=1e-4, adaptation_mode="partial"
        )
    
    model.eval()
    
    # Analyse input confidence and potentially correct
    with torch.no_grad():
        _, conf_logits = model(input_tokens)
        input_confidences = torch.sigmoid(conf_logits.squeeze()).cpu().numpy()
    
    # Apply corrections to low-confidence tokens
    corrected_input = []
    corrections_made = []
    for i, (token, conf) in enumerate(zip(corrected_sequence, input_confidences)):
        if conf < correction_threshold and token in correction_map:
            corrected_token = correction_map[token]
            corrected_input.append(corrected_token)
            corrections_made.append(f"{token} -> {corrected_token}")
        else:
            corrected_input.append(token)
    
    # Generate from corrected input
    current_sequence = corrected_input
    generated_tokens = []
    confidences = []
    
    with torch.no_grad():
        for _ in range(max_length):
            input_tokens = encode(current_sequence).unsqueeze(0).to(device)
            lm_logits, conf_logits = model(input_tokens)
            
            next_token_logits = lm_logits[0, -1, :]
            next_token_probs = F.softmax(next_token_logits / temperature, dim=-1)
            
            # Sample next token
            next_token_idx = torch.multinomial(next_token_probs, 1).item()
            next_token = idx2word[next_token_idx]
            
            if next_token == '<end>':
                break
                
            confidence = torch.sigmoid(conf_logits[0, -1, 0]).item()
            
            current_sequence.append(next_token)
            generated_tokens.append(next_token)
            confidences.append(confidence)
    
    return generated_tokens, confidences, corrected_input, corrections_made


def generate_training_data():
    base_sentences = [
        ['<start>', 'the', 'cat', 'sits', 'on', 'the', 'mat', '.', '<end>'],
        ['<start>', 'a', 'dog', 'runs', 'fast', '.', '<end>'],
        ['<start>', 'the', 'big', 'dog', 'sits', '.', '<end>'],
        ['<start>', 'a', 'small', 'cat', 'runs', '.', '<end>'],
        ['<start>', 'the', 'red', 'cat', 'sits', 'on', 'mat', '.', '<end>'],
        ['<start>', 'the', 'dog', 'runs', 'on', 'the', 'mat', '.', '<end>'],
        ['<start>', 'a', 'big', 'cat', 'sits', 'fast', '.', '<end>'],
        ['<start>', 'the', 'small', 'dog', 'runs', 'fast', '.', '<end>'],
    ]
    
    training_pairs = []
    
    for sentence in base_sentences:
        # examples (3x weight)
        for _ in range(3):
            training_pairs.append((sentence, [1.0] * len(sentence)))
        
        # Corrupted versions with varying corruption rates
        for corruption_rate in [0.1, 0.3, 0.5]:
            for _ in range(2):
                corrupted = []
                confidence = []
                
                for word in sentence:
                    if word in ['<start>', '<end>', '.']:
                        corrupted.append(word)
                        confidence.append(1.0)
                    else:
                        corrupted_word = corrupt_word(word, corruption_rate)
                        corrupted.append(corrupted_word)
                        confidence.append(0.2 if corrupted_word != word else 1.0)
                
                training_pairs.append((corrupted, confidence))
    
    return training_pairs

def train_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = CorrectionAwareTransformer(len(vocab)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=150)
    
    training_data = generate_training_data()
    print(f"Generated {len(training_data)} training examples")
    
    # Training loop
    for epoch in range(150):
        model.train()
        total_lm_loss = 0
        total_conf_loss = 0
        
        random.shuffle(training_data)
        
        for sequence, confidence in training_data:
            if len(sequence) < 2:
                continue
            
            # Prepare input and targets
            input_tokens = encode(sequence[:-1]).unsqueeze(0).to(device)
            target_tokens = encode(sequence[1:]).to(device)
            target_confidence = torch.tensor(confidence[:-1]).unsqueeze(0).to(device)
            
            # Forward pass
            lm_logits, conf_logits = model(input_tokens)
            
            # Language modeling loss
            lm_loss = F.cross_entropy(lm_logits.view(-1, len(vocab)), target_tokens.view(-1))
            
            # Confidence loss
            conf_loss = F.mse_loss(torch.sigmoid(conf_logits.squeeze(-1)), target_confidence)
            
            # Combined loss
            total_loss = lm_loss + 0.5 * conf_loss
            
            # Backward pass
            optimizer.zero_grad()
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            total_lm_loss += lm_loss.item()
            total_conf_loss += conf_loss.item()
        
        scheduler.step()
        
        if epoch % 25 == 0:
            avg_lm_loss = total_lm_loss / len(training_data)
            avg_conf_loss = total_conf_loss / len(training_data)
            print(f"Epoch {epoch}, LM Loss: {avg_lm_loss:.4f}, Conf Loss: {avg_conf_loss:.4f}")
    
    return model


# Enhanced testing with correction capabilities and TTA comparison
def test_corruption_awareness(model):
    test_cases = [
        ['teh', 'kat', 'sitz'],
        ['the', 'cat', 'sits'], 
        ['a', 'doge', 'runz'],
        ['teh', 'bigg', 'doge'],
        ['the', 'small', 'cat'],
    ]
    
    print("\n" + "="*70)
    print("Testing Corruption Awareness: Standard vs TTA")
    print("="*70)
    
    for i, test_input in enumerate(test_cases):
        print(f"\nTest {i+1}: {test_input}")
        print("-" * 50)
        
        # Standard generation
        print("STANDARD Generation:")
        generated_std, conf_std, corrected_std, corrections_std = generate_with_correction(
            model, test_input, max_length=6, correction_threshold=0.5, use_tta=False
        )
        print(f"  Generated: {generated_std}")
        print(f"  Confidences: {[f'{c:.3f}' for c in conf_std]}")
        print(f"  Full result: {' '.join(corrected_std[1:] + generated_std)}")
        
        # TTA generation
        print("\nTTA Generation (5 steps):")
        generated_tta, conf_tta, corrected_tta, corrections_tta = generate_with_correction(
            model, test_input, max_length=6, correction_threshold=0.5, 
            use_tta=True, tta_steps=5
        )
        print(f"  Generated: {generated_tta}")
        print(f"  Confidences: {[f'{c:.3f}' for c in conf_tta]}")
        print(f"  Full result: {' '.join(corrected_tta[1:] + generated_tta)}")
        
        # Compare confidence improvements
        if conf_std and conf_tta:
            avg_conf_std = sum(conf_std) / len(conf_std)
            avg_conf_tta = sum(conf_tta) / len(conf_tta)
            improvement = avg_conf_tta - avg_conf_std
            print(f"  Confidence improvement: {improvement:+.3f} ({avg_conf_std:.3f} -> {avg_conf_tta:.3f})")

def main():
    print("Training Corruption-Aware Language Model with TTA ..")
    print("-"*70)
    
    # Train model
    model = train_model()
    
    # Test corruption awareness (now includes TTA comparison)
    test_corruption_awareness(model)

if __name__ == "__main__":
    main()