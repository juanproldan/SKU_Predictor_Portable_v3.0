import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os
import joblib

# Constants
MAX_SEQUENCE_LENGTH = 50  # Original model sequence length
EMBEDDING_DIM = 100  # Original model embedding dimension
OPTIMIZED_MAX_SEQUENCE_LENGTH = 30  # Optimized model sequence length
OPTIMIZED_EMBEDDING_DIM = 128  # TEMPORARILY CHANGED: Match saved model (was 64)
OPTIMIZED_HIDDEN_DIM = 128  # TEMPORARILY CHANGED: Match saved model (was 64)


class OptimizedSKUNNModel(nn.Module):
    """
    Optimized PyTorch model for SKU prediction with improved architecture.
    This model includes bidirectional LSTM, attention mechanism, and batch normalization.
    """

    def __init__(self, cat_input_size, vocab_size, embedding_dim, hidden_size, num_classes, dropout_rate=0.3):
        super(OptimizedSKUNNModel, self).__init__()

        # Embedding layer with dropout
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.embed_dropout = nn.Dropout(dropout_rate)

        # Bidirectional LSTM for better feature extraction (no dropout for single layer)
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_size,
            batch_first=True,
            bidirectional=True
        )

        # External dropout layer for LSTM output
        self.lstm_dropout = nn.Dropout(dropout_rate)

        # Attention mechanism
        self.attention = nn.Linear(hidden_size * 2, 1)

        # Dense layers with batch normalization
        self.batch_norm1 = nn.BatchNorm1d(hidden_size * 2 + cat_input_size)
        self.fc1 = nn.Linear(hidden_size * 2 + cat_input_size, hidden_size)
        self.dropout1 = nn.Dropout(dropout_rate)

        self.batch_norm2 = nn.BatchNorm1d(hidden_size)
        self.fc2 = nn.Linear(hidden_size, num_classes)

    def attention_net(self, lstm_output):
        """Apply attention mechanism to LSTM output."""
        # lstm_output shape: (batch_size, seq_len, hidden_size*2)
        attn_weights = torch.tanh(self.attention(
            lstm_output))  # (batch_size, seq_len, 1)
        # (batch_size, seq_len, 1)
        attn_weights = torch.softmax(attn_weights, dim=1)

        # Apply attention weights to LSTM output
        # (batch_size, hidden_size*2)
        context = torch.sum(attn_weights * lstm_output, dim=1)
        return context

    def forward(self, cat_input, text_input):
        # Process text through embedding
        # (batch_size, seq_len, embedding_dim)
        embedded = self.embedding(text_input)
        embedded = self.embed_dropout(embedded)

        # Process through LSTM
        # (batch_size, seq_len, hidden_size*2)
        lstm_out, _ = self.lstm(embedded)
        lstm_out = self.lstm_dropout(lstm_out)  # Apply dropout after LSTM

        # Apply attention
        attn_out = self.attention_net(lstm_out)  # (batch_size, hidden_size*2)

        # Concatenate with categorical features
        combined = torch.cat((cat_input, attn_out), dim=1)

        # Process through dense layers
        combined = self.batch_norm1(combined)
        x = torch.relu(self.fc1(combined))
        x = self.dropout1(x)

        x = self.batch_norm2(x)
        logits = self.fc2(x)

        return logits


def load_model(model_dir):
    """
    Load the optimized PyTorch SKU NN model and its associated encoders.

    Args:
        model_dir: Directory where the model and encoders are stored

    Returns:
        model: Loaded PyTorch model
        encoders: Dictionary of loaded encoders
    """
    encoders = {}
    try:
        encoders['Make'] = joblib.load(
            os.path.join(model_dir, 'encoder_maker.joblib'))
        encoders['Model Year'] = joblib.load(
            os.path.join(model_dir, 'encoder_model.joblib'))
        encoders['Series'] = joblib.load(
            os.path.join(model_dir, 'encoder_series.joblib'))
        encoders['sku'] = joblib.load(
            os.path.join(model_dir, 'encoder_referencia.joblib'))

        # Try to load the tokenizer, but use a dummy one if it fails
        try:
            encoders['tokenizer'] = joblib.load(
                os.path.join(model_dir, 'tokenizer.joblib'))
        except Exception as e:
            print(f"Error loading tokenizer: {e}")
            # Try to import our PyTorch tokenizer first
            try:
                from utils.pytorch_tokenizer import PyTorchTokenizer
                encoders['tokenizer'] = PyTorchTokenizer(
                    num_words=10000, oov_token="<OOV>")
                print("Using PyTorchTokenizer instead.")
            except ImportError:
                # Fall back to DummyTokenizer if PyTorchTokenizer is not available
                try:
                    from utils.dummy_tokenizer import DummyTokenizer
                    encoders['tokenizer'] = DummyTokenizer(
                        num_words=10000, oov_token="<OOV>")
                    print("Using DummyTokenizer instead.")
                except ImportError:
                    # Last resort: define a minimal tokenizer inline
                    print(
                        "Warning: Could not import tokenizer classes. Using minimal inline tokenizer.")

                    class MinimalTokenizer:
                        def __init__(self):
                            self.word_index = {"<PAD>": 0, "<OOV>": 1}
                            # Add some dummy words
                            for i in range(2, 1000):
                                self.word_index[f"word_{i}"] = i

                        def texts_to_sequences(self, texts):
                            """Convert texts to sequences of integers"""
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

                    encoders['tokenizer'] = MinimalTokenizer()
                    print("Using minimal inline tokenizer as last resort.")
    except Exception as e:
        print(f"Error loading encoders: {e}")
        return None, None

    # Load optimized model
    model_path = os.path.join(model_dir, 'sku_nn_model_pytorch_optimized.pth')

    if not os.path.exists(model_path):
        print(f"No optimized model file found at {model_path}")
        return None, encoders

    try:
        # Get model parameters from encoders
        cat_input_size = 3  # Make, Model Year, Series
        vocab_size = len(encoders['tokenizer'].word_index) + 1
        num_classes = len(encoders['sku'].classes_)

        # Create model instance
        model = OptimizedSKUNNModel(
            cat_input_size=cat_input_size,
            vocab_size=vocab_size,
            embedding_dim=OPTIMIZED_EMBEDDING_DIM,
            hidden_size=OPTIMIZED_HIDDEN_DIM,
            num_classes=num_classes
        )

        # Load state dict
        model.load_state_dict(torch.load(model_path))
        model.eval()  # Set to evaluation mode

        return model, encoders
    except Exception as e:
        print(f"Error loading optimized PyTorch model: {e}")
        return None, encoders


def predict_sku(pytorch_model, encoders, maker, model_year, series, descripcion, device='cpu'):
    """
    Predict SKU using the PyTorch model.

    Args:
        pytorch_model: Loaded PyTorch model
        encoders: Dictionary of encoders
        maker: Vehicle maker
        model_year: Vehicle model year
        series: Vehicle series
        descripcion: Part description
        device: Device to run inference on ('cpu' or 'cuda')

    Returns:
        predicted_sku: Predicted SKU
        confidence: Confidence score (probability)
    """
    if pytorch_model is None or encoders is None:
        return None, 0.0

    try:
        # Move model to device
        pytorch_model = pytorch_model.to(device)

        # Normalize description
        from utils.text_utils import normalize_text
        normalized_desc = normalize_text(descripcion)

        # Encode categorical features with error handling for unseen labels
        # Try new field names first, fallback to old field names for compatibility
        try:
            maker_enc = encoders.get('maker', encoders.get('Make')).transform([maker.upper()])
        except (ValueError, AttributeError):
            print(
                f"Warning: Maker '{maker}' not seen during training. Using default value.")
            maker_enc = np.array([0])  # Use first class as default

        try:
            model_enc = encoders.get('model', encoders.get('Model Year')).transform([str(model_year)])
        except (ValueError, AttributeError):
            print(
                f"Warning: Model '{model_year}' not seen during training. Using default value.")
            model_enc = np.array([0])  # Use first class as default

        try:
            series_enc = encoders.get('series', encoders.get('Series')).transform([series.upper()])
        except (ValueError, AttributeError):
            print(
                f"Warning: Series '{series}' not seen during training. Using default value.")
            series_enc = np.array([0])  # Use first class as default

        # Tokenize and pad description
        tokenizer = encoders['tokenizer']
        sequences = tokenizer.texts_to_sequences([normalized_desc])

        # Determine which sequence length to use based on model type
        seq_length = OPTIMIZED_MAX_SEQUENCE_LENGTH

        # Manual padding (since we're not using Keras pad_sequences)
        padded_seq = [0] * seq_length
        seq = sequences[0]
        if len(seq) > seq_length:
            padded_seq = seq[:seq_length]
        else:
            padded_seq[:len(seq)] = seq

        # Convert inputs to PyTorch tensors
        cat_tensor = torch.tensor(
            [[maker_enc[0], model_enc[0], series_enc[0]]], dtype=torch.float32).to(device)
        text_tensor = torch.tensor([padded_seq], dtype=torch.long).to(device)

        # Get prediction
        with torch.no_grad():
            logits = pytorch_model(cat_tensor, text_tensor)
            probs = F.softmax(logits, dim=1)

        # Get predicted class and confidence
        confidence, predicted_idx = torch.max(probs, dim=1)
        # Try new field name first, fallback to old field name for compatibility
        sku_encoder = encoders.get('referencia', encoders.get('sku'))
        predicted_sku = sku_encoder.inverse_transform(
            predicted_idx.cpu().numpy())

        return predicted_sku[0], confidence.item()

    except Exception as e:
        print(f"Error during prediction: {e}")
        return None, 0.0
