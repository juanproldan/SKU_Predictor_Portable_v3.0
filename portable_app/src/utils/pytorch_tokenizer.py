"""
PyTorch-compatible tokenizer to replace the Keras tokenizer.
This tokenizer implements the same interface as the Keras Tokenizer
but doesn't require Keras to be installed.
"""

import re
import numpy as np
from collections import Counter


class PyTorchTokenizer:
    """
    A PyTorch-compatible tokenizer that mimics the Keras Tokenizer interface.

    This tokenizer provides the same functionality as Keras' Tokenizer but
    is implemented in pure Python without any dependencies on Keras or TensorFlow.
    """

    def __init__(self, num_words=None, oov_token="<OOV>", **kwargs):
        """
        Initialize the tokenizer.

        Args:
            num_words: Maximum number of words to keep, based on word frequency.
                       Only the most common `num_words-1` words will be kept.
            oov_token: Token to use for out-of-vocabulary words.
            **kwargs: Additional arguments (for compatibility with Keras Tokenizer)
        """
        self.num_words = num_words
        self.oov_token = oov_token
        self.word_counts = {}
        self.word_index = {}
        self.index_word = {}
        self.word_docs = {}
        self.document_count = 0

        # Always include padding token at index 0
        self.word_index["<PAD>"] = 0
        self.index_word[0] = "<PAD>"

        # Add OOV token if provided
        if oov_token is not None:
            self.word_index[oov_token] = 1
            self.index_word[1] = oov_token

        # For compatibility with existing models, initialize with dummy words
        # to match the expected vocabulary size (1001)
        for i in range(2, 1001):
            self.word_index[f"word_{i-2}"] = i
            self.index_word[i] = f"word_{i-2}"

    def fit_on_texts(self, texts):
        """
        Update internal vocabulary based on a list of texts.

        Args:
            texts: List of strings to train the tokenizer on.
        """
        # Count word occurrences across all texts
        for text in texts:
            self.document_count += 1

            # Normalize and tokenize text
            words = self._tokenize(text)

            # Update word counts
            for word in words:
                if word in self.word_counts:
                    self.word_counts[word] += 1
                else:
                    self.word_counts[word] = 1

            # Update word_docs (for IDF calculation if needed)
            for word in set(words):
                if word in self.word_docs:
                    self.word_docs[word] += 1
                else:
                    self.word_docs[word] = 1

        # Sort words by frequency
        wcounts = list(self.word_counts.items())
        wcounts.sort(key=lambda x: x[1], reverse=True)

        # Build word_index mapping
        # Start from 2 because 0 is reserved for padding and 1 for OOV
        idx = 2
        for word, count in wcounts:
            if self.num_words and idx >= self.num_words:
                break
            self.word_index[word] = idx
            self.index_word[idx] = word
            idx += 1

    def texts_to_sequences(self, texts):
        """
        Transform each text in texts to a sequence of integers.

        Args:
            texts: List of strings to convert to sequences.

        Returns:
            List of sequences (lists of integers).
        """
        sequences = []
        for text in texts:
            words = self._tokenize(text)
            seq = []
            for word in words:
                if word in self.word_index:
                    seq.append(self.word_index[word])
                elif self.oov_token is not None:
                    # Use OOV token index (1)
                    seq.append(self.word_index[self.oov_token])
            sequences.append(seq)
        return sequences

    def sequences_to_texts(self, sequences):
        """
        Convert sequences back to texts.

        Args:
            sequences: List of sequences (lists of integers).

        Returns:
            List of strings.
        """
        texts = []
        for seq in sequences:
            words = []
            for idx in seq:
                if idx in self.index_word:
                    words.append(self.index_word[idx])
                elif self.oov_token is not None:
                    words.append(self.oov_token)
            texts.append(" ".join(words))
        return texts

    def _tokenize(self, text):
        """
        Tokenize a text string into words.

        Args:
            text: String to tokenize.

        Returns:
            List of words.
        """
        # Convert to lowercase and split by whitespace
        return text.lower().split()

    def pad_sequences(self, sequences, maxlen=None, padding='pre', truncating='pre', value=0):
        """
        Pad sequences to the same length.

        Args:
            sequences: List of sequences (lists of integers).
            maxlen: Maximum length of all sequences. If None, uses the length of the longest sequence.
            padding: 'pre' or 'post', pad either before or after each sequence.
            truncating: 'pre' or 'post', remove values from sequences larger than maxlen.
            value: Value to pad with.

        Returns:
            Numpy array of padded sequences.
        """
        if not maxlen:
            maxlen = max(len(seq) for seq in sequences)

        padded_sequences = []
        for seq in sequences:
            if len(seq) > maxlen:
                if truncating == 'pre':
                    seq = seq[-maxlen:]
                else:
                    seq = seq[:maxlen]

            pad_length = maxlen - len(seq)
            if padding == 'pre':
                padded_seq = [value] * pad_length + seq
            else:
                padded_seq = seq + [value] * pad_length

            padded_sequences.append(padded_seq)

        return np.array(padded_sequences)
