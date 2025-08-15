"""
A dummy tokenizer class to replace the Keras tokenizer.
This is used when the Keras tokenizer is not available.
"""

import re
from collections import Counter


class DummyTokenizer:
    """
    A simple tokenizer class that mimics the Keras Tokenizer interface.
    This improved version builds a basic vocabulary from the input text
    when texts_to_sequences is called, making it more effective even without
    explicit training.
    """

    def __init__(self, num_words=10000, oov_token="<OOV>"):
        """
        Initialize the tokenizer.

        Args:
            num_words: Maximum number of words to keep
            oov_token: Token to use for out-of-vocabulary words
        """
        self.num_words = num_words
        self.oov_token = oov_token
        self.word_index = {"<PAD>": 0, "<OOV>": 1}
        self._is_fitted = False

        # For compatibility with existing models, initialize with dummy words
        # to match the expected vocabulary size (1001)
        for i in range(2, 1001):
            self.word_index[f"word_{i-2}"] = i

    def _build_vocab_on_first_use(self, texts):
        """
        Build a vocabulary from the provided texts on first use.
        This allows the tokenizer to work better even without explicit training.
        """
        if self._is_fitted:
            return

        # Count word frequencies across all texts
        word_counts = Counter()
        for text in texts:
            words = text.lower().split()
            word_counts.update(words)

        # Add most common words to the vocabulary
        # Start from index 2 (0 is PAD, 1 is OOV)
        for idx, (word, _) in enumerate(word_counts.most_common(self.num_words - 2)):
            self.word_index[word] = idx + 2

        self._is_fitted = True

    def texts_to_sequences(self, texts):
        """
        Convert a list of texts to a list of sequences.
        If the tokenizer hasn't been fitted yet, it will build a vocabulary first.

        Args:
            texts: List of strings

        Returns:
            List of sequences (lists of integers)
        """
        # Build vocabulary on first use
        if not self._is_fitted:
            self._build_vocab_on_first_use(texts)

        sequences = []
        for text in texts:
            words = text.lower().split()
            seq = []
            for word in words:
                if word in self.word_index:
                    seq.append(self.word_index[word])
                else:
                    seq.append(self.word_index["<OOV>"])
            sequences.append(seq)
        return sequences

    def fit_on_texts(self, texts):
        """
        Update internal vocabulary based on a list of texts.

        Args:
            texts: List of strings to train the tokenizer on.
        """
        # Reset the vocabulary
        self.word_index = {"<PAD>": 0, "<OOV>": 1}

        # Count word frequencies
        word_counts = Counter()
        for text in texts:
            words = text.lower().split()
            word_counts.update(words)

        # Add most common words to the vocabulary
        for idx, (word, _) in enumerate(word_counts.most_common(self.num_words - 2)):
            self.word_index[word] = idx + 2

        self._is_fitted = True
