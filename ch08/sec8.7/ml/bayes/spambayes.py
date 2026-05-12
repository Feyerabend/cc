

import math
from collections import defaultdict, Counter

class NaiveBayesClassifier:
    def __init__(self):
        self.class_word_counts = defaultdict(Counter)
        self.class_doc_counts = defaultdict(int)
        self.vocab = set()
        self.total_docs = 0

    def train(self, documents, labels):
        for doc, label in zip(documents, labels):
            self.total_docs += 1
            self.class_doc_counts[label] += 1
            for word in doc.split():
                self.class_word_counts[label][word] += 1
                self.vocab.add(word)

    def predict(self, doc):
        words = doc.split()
        scores = {}
        vocab_size = len(self.vocab)

        for cls in self.class_doc_counts:
            log_prob = math.log(self.class_doc_counts[cls] / self.total_docs)
            total_words = sum(self.class_word_counts[cls].values())

            for word in words:
                word_count = self.class_word_counts[cls][word]
                # Laplace smoothing
                word_prob = (word_count + 1) / (total_words + vocab_size)
                log_prob += math.log(word_prob)

            scores[cls] = log_prob

        return max(scores, key=scores.get)

# Example usage
if __name__ == "__main__":
    # Sample data
    documents = [
        "free money now",
        "limited time offer",
        "hello friend",
        "meeting tomorrow",
        "urgent response needed",
        "discount available",
        "project deadline approaching"
    ]
    labels = ["spam", "spam", "ham", "ham", "spam", "spam", "ham"]

    # Create and train the classifier
    classifier = NaiveBayesClassifier()
    classifier.train(documents, labels)

    # Test the classifier
    test_docs = [
        "free gift card",
        "project update meeting",
        "limited time discount"
    ]

    for doc in test_docs:
        print(f"Document: '{doc}' is classified as: {classifier.predict(doc)}")

# This is a simple implementation of a Naive Bayes classifier for spam detection.
# It uses Laplace smoothing to handle words not seen in the training data.
# The classifier is trained on a small set of documents and labels, and then
# it predicts the class of new documents based on the learned probabilities.
# The example usage at the end demonstrates how to train the classifier and
# test it with new documents.

