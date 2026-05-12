import numpy as np
from collections import defaultdict, Counter
import re
from typing import List, Tuple, Dict
from PIL import Image, ImageDraw

class SimpleWord2Vec:
    def __init__(self, vector_size=50, window_size=4, learning_rate=0.01, epochs=200):
        self.vector_size = vector_size
        self.window_size = window_size
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.vocab_size = 0
        self.W1 = None
        self.W2 = None
        
    def preprocess_text(self, text: str) -> List[str]:
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        return words
    
    def build_vocabulary(self, corpus: List[str], min_count=2):
        stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'and', 'are', 'is'}
        word_counts = Counter()
        for sentence in corpus:
            words = self.preprocess_text(sentence)
            word_counts.update(words)
        filtered_words = [word for word, count in word_counts.items() if count >= min_count and word not in stopwords]
        self.word_to_idx = {word: idx for idx, word in enumerate(filtered_words)}
        self.idx_to_word = {idx: word for word, idx in self.word_to_idx.items()}
        self.vocab_size = len(self.word_to_idx)
        print(f"Vocabulary size: {self.vocab_size}")
        print(f"Vocabulary: {list(self.word_to_idx.keys())}")
    
    def generate_training_data(self, corpus: List[str]) -> List[Tuple[int, int]]:
        training_data = []
        for sentence in corpus:
            words = self.preprocess_text(sentence)
            word_indices = [self.word_to_idx[word] for word in words if word in self.word_to_idx]
            for i, center_word_idx in enumerate(word_indices):
                for j in range(max(0, i - self.window_size), 
                              min(len(word_indices), i + self.window_size + 1)):
                    if i != j:
                        context_word_idx = word_indices[j]
                        training_data.append((center_word_idx, context_word_idx))
        return training_data
    
    def normalize_vectors(self):
        norms = np.linalg.norm(self.W1, axis=1, keepdims=True)
        self.W1 = self.W1 / (norms + 1e-10)
    
    def train(self, corpus: List[str], negative_samples=5):
        print("Building vocabulary...")
        self.build_vocabulary(corpus, min_count=2)
        self.W1 = np.random.uniform(-0.1, 0.1, (self.vocab_size, self.vector_size))
        self.W2 = np.random.uniform(-0.1, 0.1, (self.vector_size, self.vocab_size))
        
        print("Generating training data...")
        training_data = self.generate_training_data(corpus)
        print(f"Training pairs: {len(training_data)}")
        
        print("Training model...")
        losses = []
        for epoch in range(self.epochs):
            total_loss = 0
            np.random.shuffle(training_data)
            lr = self.learning_rate * (1 - epoch / self.epochs)  # Linear decay
            for center_word_idx, context_word_idx in training_data:
                h = self.W1[center_word_idx].copy()
                u_pos = np.dot(h, self.W2[:, context_word_idx])
                y_pred_pos = 1 / (1 + np.exp(-u_pos))
                loss = -np.log(y_pred_pos + 1e-10)
                
                error_pos = y_pred_pos - 1
                dW2_pos = error_pos * h
                dW1_pos = error_pos * self.W2[:, context_word_idx]
                
                negative_indices = np.random.choice(self.vocab_size, negative_samples)
                for neg_idx in negative_indices:
                    if neg_idx != context_word_idx:
                        u_neg = np.dot(h, self.W2[:, neg_idx])
                        y_pred_neg = 1 / (1 + np.exp(-u_neg))
                        loss -= np.log(1 - y_pred_neg + 1e-10)
                        error_neg = y_pred_neg
                        dW2_neg = error_neg * h
                        dW1_neg = error_neg * self.W2[:, neg_idx]
                        self.W2[:, neg_idx] -= lr * np.clip(dW2_neg, -1.0, 1.0)
                        self.W1[center_word_idx] -= lr * np.clip(dW1_neg, -1.0, 1.0)
                
                self.W2[:, context_word_idx] -= lr * np.clip(dW2_pos, -1.0, 1.0)
                self.W1[center_word_idx] -= lr * np.clip(dW1_pos, -1.0, 1.0)
                
                total_loss += loss
            avg_loss = total_loss / len(training_data)
            losses.append(avg_loss)
            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Average Loss: {avg_loss:.4f}")
        
        self.normalize_vectors()
        self.plot_losses(losses)
        return losses
    
    def plot_losses(self, losses: List[float]):
        width, height = 800, 600
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        margin = 50
        plot_width = width - 2 * margin
        plot_height = height - 2 * margin
        
        max_loss = max(losses) if losses else 1.0
        min_loss = min(losses) if losses else 0.0
        if max_loss == min_loss:
            max_loss += 1e-10
        
        draw.line((margin, height - margin, width - margin, height - margin), fill='black', width=2)
        draw.line((margin, height - margin, margin, margin), fill='black', width=2)
        
        draw.text((width - margin + 10, height - margin - 10), "Epoch", fill='black')
        draw.text((margin - 30, margin - 30), "Loss", fill='black')
        
        num_xticks = 10
        num_yticks = 10
        for i in range(num_xticks + 1):
            x = margin + i * plot_width // num_xticks
            epoch = i * self.epochs // num_xticks
            draw.line((x, height - margin, x, height - margin + 5), fill='black', width=1)
            draw.text((x - 10, height - margin + 10), str(epoch), fill='black')
        
        for i in range(num_yticks + 1):
            y = height - margin - i * plot_height // num_yticks
            loss = min_loss + i * (max_loss - min_loss) / num_yticks
            draw.line((margin - 5, y, margin, y), fill='black', width=1)
            draw.text((margin - 40, y - 5), f"{loss:.2f}", fill='black')
        
        points = []
        for i, loss in enumerate(losses):
            x = margin + (i / (len(losses) - 1)) * plot_width
            y = height - margin - ((loss - min_loss) / (max_loss - min_loss + 1e-10)) * plot_height
            points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill='blue', width=2)
        
        img.save("loss_plot.png")
        print("Loss plot saved as 'loss_plot.png'")
    
    def get_word_vector(self, word: str) -> np.ndarray:
        if word not in self.word_to_idx:
            raise ValueError(f"Word '{word}' not in vocabulary")
        word_idx = self.word_to_idx[word]
        return self.W1[word_idx]
    
    def most_similar(self, word: str, top_k=5) -> List[Tuple[str, float]]:
        if word not in self.word_to_idx:
            raise ValueError(f"Word '{word}' not in vocabulary")
        word_vector = self.get_word_vector(word)
        similarities = []
        for other_word, idx in self.word_to_idx.items():
            if other_word != word:
                other_vector = self.W1[idx]
                similarity = np.dot(word_vector, other_vector) / (
                    np.linalg.norm(word_vector) * np.linalg.norm(other_vector) + 1e-10
                )
                similarities.append((other_word, similarity))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

if __name__ == "__main__":
    corpus = [
        "The cat sat on the mat",
        "The dog ran in the park",
        "A cat and a dog are pets",
        "I love my pet cat",
        "The dog plays in the garden",
        "Cats and dogs are animals",
        "The mat is on the floor",
        "Animals need food and water",
        "My cat likes to sleep",
        "The dog barks at strangers",
        "Cats and dogs are common pets",
        "The cat and dog play together",
        "My pet cat sleeps on the mat",
        "Dogs and cats need food daily",
        "Animals like cats are furry",
        "The cat chased the mouse",
        "Dogs are loyal pets",
        "Cats love to climb trees",
        "The dog wags its tail",
        "Pets like cats and dogs are friendly",
        "Cats and dogs live in houses",
        "Pets like cats need care",
        "The dog and cat are friends",
        "Animals such as cats are mammals",
        "My cat and dog sleep together"
    ]
    model = SimpleWord2Vec(vector_size=50, window_size=4, learning_rate=0.01, epochs=200)
    model.train(corpus, negative_samples=5)
    try:
        print("\nWord vector for 'cat':")
        cat_vector = model.get_word_vector('cat')
        print(f"Vector shape: {cat_vector.shape}")
        print(f"First 5 dimensions: {cat_vector[:5]}")
        print("\nMost similar words to 'cat':")
        similar_words = model.most_similar('cat', top_k=3)
        for word, similarity in similar_words:
            print(f"{word}: {similarity:.4f}")
        print("\nMost similar words to 'dog':")
        similar_words = model.most_similar('dog', top_k=3)
        for word, similarity in similar_words:
            print(f"{word}: {similarity:.4f}")
    except ValueError as e:
        print(f"Error: {e}")