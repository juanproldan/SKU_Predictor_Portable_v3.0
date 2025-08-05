"""
Optimized PyTorch training script for SKU Neural Network Predictor.
This version includes performance optimizations for faster training.
"""

import pandas as pd
import numpy as np
import os
import sys
import sqlite3
import joblib
import time
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
try:
    from utils.pytorch_tokenizer import PyTorchTokenizer
    from utils.text_utils import normalize_text
except ImportError:
    from utils.dummy_tokenizer import DummyTokenizer
    try:
        from utils.text_utils import normalize_text
    except ImportError:
        # Fallback normalize function if text_utils not available
        def normalize_text(text, **kwargs):
            return text.lower().strip()

# --- Configuration ---
def get_base_path():
    """Get the base path for the application, works for both script and executable."""
    if getattr(sys, 'frozen', False):
        # Running as executable - executable is in client folder root
        return os.path.dirname(sys.executable)
    else:
        # Running as script - script is in src/, need to find client folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)  # Go up from src/ to project root
        return os.path.join(project_root, "Fixacar_SKU_Predictor_CLIENT")

BASE_PATH = get_base_path()
DB_PATH = os.path.join(BASE_PATH, "Fixacar_SKU_Predictor_CLIENT", "Source_Files", "processed_consolidado.db")
MAESTRO_PATH = os.path.join(BASE_PATH, "Fixacar_SKU_Predictor_CLIENT", "Source_Files", "Maestro.xlsx")  # Optional, if it contains useful data
VIN_MODEL_DIR = os.path.join(BASE_PATH, "Fixacar_SKU_Predictor_CLIENT", "models")  # Directory for VIN detail predictor models
SKU_NN_MODEL_DIR = os.path.join(BASE_PATH, "Fixacar_SKU_Predictor_CLIENT", "models", "sku_nn")  # Directory for SKU NN model and preprocessors
MIN_SKU_FREQUENCY = 3  # Minimum times an SKU must appear to be included in training
VOCAB_SIZE = 10000  # Max number of words to keep in the vocabulary
MAX_SEQUENCE_LENGTH = 30  # Reduced from 50 to 30
EMBEDDING_DIM = 128  # Increased from 64 to 128 for better capacity
HIDDEN_DIM = 128     # Increased from 64 to 128 for better learning
BATCH_SIZE = 256  # Optimized for overnight training (will auto-adjust if needed)
EPOCHS = 100  # More epochs for better convergence
LEARNING_RATE = 0.001
# Memory optimization: reduce batch size if training data is very large
ADAPTIVE_BATCH_SIZE = True  # Enable adaptive batch sizing
VIN_BATCH_SIZE = 5000  # Process VINs in larger batches for full dataset
# Set to a number (e.g., 50000) to use a subset of data, or None for all data
SAMPLE_SIZE = None  # Using full dataset for production training

def cleanup_old_model_checkpoints(model_dir, keep_latest=3):
    """
    Clean up old model checkpoint files, keeping only the latest N versions.

    Args:
        model_dir: Directory containing model files
        keep_latest: Number of latest timestamped models to keep (default: 3)
    """
    try:
        # Find all timestamped model files
        pattern = os.path.join(model_dir, "sku_nn_model_pytorch_optimized_*.pth")
        model_files = glob.glob(pattern)

        # Exclude the default model file (without timestamp)
        default_model = os.path.join(model_dir, "sku_nn_model_pytorch_optimized.pth")
        model_files = [f for f in model_files if f != default_model]

        if len(model_files) <= keep_latest:
            print(f"  Model cleanup: {len(model_files)} checkpoint files found, keeping all")
            return

        # Sort by modification time (newest first)
        model_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        # Keep the latest N files, delete the rest
        files_to_keep = model_files[:keep_latest]
        files_to_delete = model_files[keep_latest:]

        print(f"  Model cleanup: Found {len(model_files)} checkpoint files")
        print(f"  Keeping latest {keep_latest}: {[os.path.basename(f) for f in files_to_keep]}")
        print(f"  Deleting {len(files_to_delete)} old checkpoints...")

        deleted_count = 0
        total_size_saved = 0
        for file_path in files_to_delete:
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                total_size_saved += file_size
                print(f"    Deleted: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"    Warning: Could not delete {os.path.basename(file_path)}: {e}")

        if deleted_count > 0:
            size_mb = total_size_saved / (1024 * 1024)
            print(f"  ✅ Cleanup complete: Deleted {deleted_count} files, saved {size_mb:.1f} MB")

    except Exception as e:
        print(f"  Warning: Model cleanup failed: {e}")

# --- Training Mode Configuration ---
import argparse
TRAINING_MODE = "full"  # Default to full training, can be overridden by command line

# --- Load VIN Predictor Models ---
try:
    from train_vin_predictor import extract_vin_features_production
    model_maker = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'maker_model.joblib'))
    encoder_x_maker = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'maker_encoder_x.joblib'))
    encoder_y_maker = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'maker_encoder_y.joblib'))

    model_model = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'model_model.joblib'))
    encoder_x_model = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'model_encoder_x.joblib'))
    encoder_y_model = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'model_encoder_y.joblib'))

    model_series = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'series_model.joblib'))
    encoder_x_series = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'series_encoder_x.joblib'))
    encoder_y_series = joblib.load(os.path.join(
        VIN_MODEL_DIR, 'series_encoder_y.joblib'))
    print("VIN detail prediction models loaded successfully.")
except Exception as e:
    print(
        f"Error loading VIN detail prediction models: {e}. This script cannot proceed without them.")
    model_maker = None  # Ensure it's None so script can exit if needed


def predict_vin_details_batch(vins):
    """Process VIN predictions in batches for better performance."""
    if not model_maker or not model_model or not model_series:
        return [{"maker": "N/A", "model": "N/A", "series": "N/A"} for _ in vins]

    results = []
    for vin in vins:
        features = extract_vin_features_production(vin)
        if not features:
            results.append(
                {"maker": "N/A", "model": "N/A", "series": "N/A"})
            continue

        details = {"maker": "N/A", "model": "N/A", "series": "N/A"}
        try:
            # Predict Make - Use DataFrame with proper column names
            import pandas as pd
            wmi_df = pd.DataFrame([[features['wmi']]], columns=['wmi'])
            wmi_encoded = encoder_x_maker.transform(wmi_df)
            if -1 not in wmi_encoded:
                pred_encoded = model_maker.predict(wmi_encoded)
                if pred_encoded[0] != -1:
                    details['maker'] = encoder_y_maker.inverse_transform(
                        pred_encoded.reshape(-1, 1))[0]

            # Predict Model Year - Use DataFrame with proper column names
            year_df = pd.DataFrame([[features['year_code']]], columns=['year_code'])
            year_code_encoded = encoder_x_model.transform(year_df)
            if -1 not in year_code_encoded:
                pred_encoded = model_model.predict(year_code_encoded)
                if pred_encoded[0] != -1:
                    details['model'] = encoder_y_model.inverse_transform(
                        pred_encoded.reshape(-1, 1))[0]

            # Predict Series - Use DataFrame with proper column names
            series_df = pd.DataFrame([[features['wmi'], features['vds_full']]],
                                   columns=['wmi', 'vds_full'])
            series_features_encoded = encoder_x_series.transform(series_df)
            if -1 not in series_features_encoded[0]:
                pred_encoded = model_series.predict(
                    series_features_encoded)
                if pred_encoded[0] != -1:
                    details['series'] = encoder_y_series.inverse_transform(
                        pred_encoded.reshape(-1, 1))[0]
        except Exception as e:
            print(f"Warning: Error predicting details for VIN {vin}: {e}")

        results.append({k: str(v.item()) if isinstance(
            v, np.ndarray) else str(v) for k, v in details.items()})

    return results


def load_and_preprocess_data(incremental_mode=False, days_back=7):
    """Loads data from DB, preprocesses for NN training with optimizations.

    Args:
        incremental_mode (bool): If True, only load recent data for incremental training
        days_back (int): Number of days back to load for incremental training
    """
    if not model_makerr:  # Check if VIN models loaded
        print("VIN detail prediction models are not available. Cannot preprocess data.")
        return None

    start_time = time.time()

    if incremental_mode:
        print(f"Loading incremental data from {DB_PATH} (last {days_back} days)...")
        # For incremental training, load only recent data
        # Assuming there's a timestamp column or we can use row IDs
        conn = sqlite3.connect(DB_PATH)

        # Get the latest records (assuming higher IDs are newer)
        # This is a simple approach - in production you'd want actual timestamps
        total_query = "SELECT COUNT(*) FROM processed_consolidado WHERE referencia IS NOT NULL"
        total_count = pd.read_sql_query(total_query, conn).iloc[0, 0]

        # Take approximately the last week's worth of data (estimate)
        # Assuming roughly equal distribution, take last 2% for weekly updates
        recent_limit = max(1000, int(total_count * 0.02))  # At least 1000 records

        query = f"""
        SELECT vin_number, descripcion, normalized_descripcion, referencia
        FROM processed_consolidado
        WHERE referencia IS NOT NULL
        ORDER BY ROWID DESC
        LIMIT {recent_limit}
        """
        print(f"Loading approximately {recent_limit} recent records for incremental training...")
    else:
        print(f"Loading full dataset from {DB_PATH}...")
        conn = sqlite3.connect(DB_PATH)

        # Optionally limit the data size for faster testing
        if SAMPLE_SIZE:
            query = f"SELECT vin_number, descripcion, normalized_descripcion, referencia FROM processed_consolidado WHERE referencia IS NOT NULL LIMIT {SAMPLE_SIZE}"
        else:
            query = "SELECT vin_number, descripcion, normalized_descripcion, referencia FROM processed_consolidado WHERE referencia IS NOT NULL"

    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return None

    df_history = pd.read_sql_query(query, conn)
    conn.close()

    print(
        f"Loaded {len(df_history)} records from processed_consolidado in {time.time() - start_time:.2f} seconds.")

    # Process Maestro data if available
    if os.path.exists(MAESTRO_PATH):
        try:
            df_maestro = pd.read_excel(MAESTRO_PATH)
            print(
                f"Loaded {len(df_maestro)} records from Maestro.xlsx (integration pending).")
        except Exception as e:
            print(f"Warning: Could not load or process Maestro.xlsx: {e}")

    df = df_history.copy()
    if df.empty:
        print("No data available after loading.")
        return None

    # Process VIN details in batches with progress tracking
    print("Predicting VIN details for historical data (in batches)...")
    vin_details_list = []
    total_vins = len(df)
    total_batches = (total_vins + VIN_BATCH_SIZE - 1) // VIN_BATCH_SIZE

    # Progress tracking variables
    start_vin_time = time.time()
    last_update_time = start_vin_time
    update_interval = 10  # seconds

    for batch_idx, i in enumerate(range(0, total_vins, VIN_BATCH_SIZE)):
        batch_end = min(i + VIN_BATCH_SIZE, total_vins)

        # Calculate and display progress
        progress_pct = (batch_idx + 1) / total_batches * 100
        current_time = time.time()
        elapsed_time = current_time - start_vin_time

        # Only update progress at intervals to avoid console spam
        if current_time - last_update_time >= update_interval or batch_idx == 0 or batch_idx == total_batches - 1:
            if batch_idx > 0:
                # Estimate remaining time
                time_per_batch = elapsed_time / (batch_idx + 1)
                remaining_batches = total_batches - (batch_idx + 1)
                remaining_time = time_per_batch * remaining_batches

                # Convert to hours, minutes, seconds
                r_hours, r_remainder = divmod(remaining_time, 3600)
                r_minutes, r_seconds = divmod(r_remainder, 60)

                # Format the time string
                if r_hours > 0:
                    time_str = f"{int(r_hours)}h {int(r_minutes)}m remaining"
                elif r_minutes > 0:
                    time_str = f"{int(r_minutes)}m {int(r_seconds)}s remaining"
                else:
                    time_str = f"{int(r_seconds)}s remaining"

                print(
                    f"  Processing VINs {i+1}-{batch_end} of {total_vins} ({progress_pct:.1f}%) - {time_str}")
            else:
                print(
                    f"  Processing VINs {i+1}-{batch_end} of {total_vins} ({progress_pct:.1f}%)")

            last_update_time = current_time

        # Process the batch
        batch_vins = df['vin_number'].iloc[i:batch_end].tolist()
        batch_results = predict_vin_details_batch(batch_vins)
        vin_details_list.extend(batch_results)

    # Print total time for VIN processing
    total_vin_time = time.time() - start_vin_time
    v_hours, v_remainder = divmod(total_vin_time, 3600)
    v_minutes, v_seconds = divmod(v_remainder, 60)

    if v_hours > 0:
        print(
            f"VIN processing completed in {int(v_hours)}h {int(v_minutes)}m {v_seconds:.1f}s")
    elif v_minutes > 0:
        print(
            f"VIN processing completed in {int(v_minutes)}m {v_seconds:.1f}s")
    else:
        print(f"VIN processing completed in {v_seconds:.1f}s")

    df_vin_details = pd.DataFrame(vin_details_list)
    df = pd.concat([df.reset_index(drop=True),
                   df_vin_details.reset_index(drop=True)], axis=1)

    # Clean data
    df.dropna(subset=['maker', 'model', 'series',
              'descripcion', 'referencia'], inplace=True)
    df = df[(df['maker'] != 'N/A') & (df['model']
                                     != 'N/A') & (df['series'] != 'N/A')]
    print(f"Records after VIN prediction and NA drop: {len(df)}")

    if df.empty:
        print("No data remaining after VIN detail prediction and cleaning.")
        return None

    # Filter rare SKUs
    sku_counts = df['referencia'].value_counts()
    common_skus = sku_counts[sku_counts >= MIN_SKU_FREQUENCY].index
    df = df[df['referencia'].isin(common_skus)]
    print(
        f"Records after filtering rare SKUs (min_freq={MIN_SKU_FREQUENCY}): {len(df)}")

    if df.empty or len(df) < 50:
        print("Insufficient data after filtering. Cannot train SKU predictor.")
        return None

    # Encode categorical features
    categorical_features = ['maker', 'model', 'series']
    encoders = {}
    for col in categorical_features:
        le = LabelEncoder()
        df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        print(f"Encoded '{col}', found {len(le.classes_)} unique values.")

    sku_encoder = LabelEncoder()
    df['referencia_encoded'] = sku_encoder.fit_transform(df['referencia'])
    encoders['referencia'] = sku_encoder
    num_classes = len(sku_encoder.classes_)
    print(f"Encoded 'referencia', found {num_classes} unique SKUs (classes).")

    # Save encoders
    os.makedirs(SKU_NN_MODEL_DIR, exist_ok=True)
    for name, encoder in encoders.items():
        joblib.dump(encoder, os.path.join(
            SKU_NN_MODEL_DIR, f'encoder_{name}.joblib'))

    # Tokenize and pad text descriptions
    print("Tokenizing and padding 'normalized_descripcion'...")
    # Note: descriptions are already processed in the database by unified_consolidado_processor.py
    # which uses unified_text_preprocessing() with user corrections, abbreviations, synonyms, and linguistic variations
    descriptions = df['normalized_descripcion'].astype(str).tolist()

    # Additional normalization to ensure consistency (fallback for any edge cases)
    descriptions = [normalize_text(desc, expand_linguistic_variations=True) for desc in descriptions]

    # Create tokenizer
    try:
        tokenizer = PyTorchTokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
        print("Using PyTorchTokenizer for training.")
    except NameError:
        tokenizer = DummyTokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
        print("Using DummyTokenizer for training.")

    # Fit tokenizer and convert to sequences
    tokenizer.fit_on_texts(descriptions)
    print(f"Found {len(tokenizer.word_index)} unique tokens.")

    sequences = tokenizer.texts_to_sequences(descriptions)

    # Optimized padding
    padded_sequences = tokenizer.pad_sequences(
        sequences,
        maxlen=MAX_SEQUENCE_LENGTH,
        padding='post',
        truncating='post'
    )

    print(f"Padded sequences shape: {padded_sequences.shape}")

    # Save tokenizer
    joblib.dump(tokenizer, os.path.join(SKU_NN_MODEL_DIR, 'tokenizer.joblib'))

    # Prepare features
    X_cat = df[[col + '_encoded' for col in categorical_features]].values
    X_text = padded_sequences
    y_encoded = df['referencia_encoded'].values

    print(
        f"Data preprocessing completed in {time.time() - start_time:.2f} seconds.")
    return X_cat, X_text, y_encoded, encoders, tokenizer, num_classes, len(tokenizer.word_index) + 1


# --- Optimized PyTorch Neural Network Model ---
class OptimizedSKUNNModel(nn.Module):
    def __init__(self, cat_input_size, vocab_size, embedding_dim, hidden_size, num_classes, dropout_rate=0.3):
        super(OptimizedSKUNNModel, self).__init__()

        # Embedding layer with dropout
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.embed_dropout = nn.Dropout(dropout_rate)

        # Bidirectional LSTM for better feature extraction
        # Note: dropout only applies when num_layers > 1, so we use separate dropout layer
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_size,
            batch_first=True,
            bidirectional=True,
            num_layers=1  # Single layer, no internal dropout
        )

        # LSTM output dropout
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


def load_existing_model_for_incremental(model_path, cat_input_size, vocab_size, num_classes):
    """Load existing model for incremental training."""
    try:
        model = OptimizedSKUNNModel(
            cat_input_size=cat_input_size,
            vocab_size=vocab_size,
            embedding_dim=EMBEDDING_DIM,
            hidden_size=HIDDEN_DIM,
            num_classes=num_classes
        )
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        print(f"Successfully loaded existing model from {model_path}")
        return model
    except Exception as e:
        print(f"Error loading existing model: {e}")
        print("Will create new model instead...")
        return None


# --- Main Execution ---
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Train SKU Neural Network')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='full',
                        help='Training mode: full (default) or incremental')
    parser.add_argument('--days', type=int, default=7,
                        help='Days back for incremental training (default: 7)')
    args = parser.parse_args()

    TRAINING_MODE = args.mode
    incremental_mode = (TRAINING_MODE == 'incremental')

    if not model_maker:  # Critical dependency check
        print("Exiting: VIN detail prediction models failed to load.")
    else:
        mode_text = "Incremental" if incremental_mode else "Full"
        print(f"--- Starting {mode_text} SKU Neural Network Predictor Training (PyTorch) ---")
        start_time = time.time()

        # Load and preprocess data
        results = load_and_preprocess_data(incremental_mode=incremental_mode, days_back=args.days)

        if results is not None:
            X_cat, X_text, y_encoded, encoders, tokenizer, num_classes, vocab_size = results

            # Split data into training and validation sets
            X_cat_train, X_cat_val, X_text_train, X_text_val, y_train, y_val = train_test_split(
                X_cat, X_text, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
            )

            print(f"\nData preparation successful. Shapes:")
            print(
                f"  X_cat_train: {X_cat_train.shape}, X_text_train: {X_text_train.shape}, y_train: {y_train.shape}")
            print(
                f"  X_cat_val: {X_cat_val.shape}, X_text_val: {X_text_val.shape}, y_val: {y_val.shape}")
            print(f"Number of classes (SKUs): {num_classes}")
            print(f"Tokenizer vocabulary size: {vocab_size}")

            # Convert to PyTorch tensors
            X_cat_train_tensor = torch.tensor(X_cat_train, dtype=torch.float32)
            X_text_train_tensor = torch.tensor(X_text_train, dtype=torch.long)
            y_train_tensor = torch.tensor(y_train, dtype=torch.long)

            X_cat_val_tensor = torch.tensor(X_cat_val, dtype=torch.float32)
            X_text_val_tensor = torch.tensor(X_text_val, dtype=torch.long)
            y_val_tensor = torch.tensor(y_val, dtype=torch.long)

            # Create DataLoader with optimized batch size
            train_dataset = TensorDataset(
                X_cat_train_tensor, X_text_train_tensor, y_train_tensor)
            val_dataset = TensorDataset(
                X_cat_val_tensor, X_text_val_tensor, y_val_tensor)

            train_loader = DataLoader(
                train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
            val_loader = DataLoader(
                val_dataset, batch_size=BATCH_SIZE, num_workers=0)

            # Set up device (CPU/GPU)
            device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu")
            print(f"Using device: {device}")

            # Create or load model based on training mode
            if incremental_mode:
                # Try to load existing model for incremental training
                existing_model_path = os.path.join(SKU_NN_MODEL_DIR, 'sku_nn_model_pytorch_optimized.pth')
                model = load_existing_model_for_incremental(
                    existing_model_path,
                    X_cat_train.shape[1],
                    vocab_size,
                    num_classes
                )

                if model is None:
                    print("Creating new model for incremental training...")
                    model = OptimizedSKUNNModel(
                        cat_input_size=X_cat_train.shape[1],
                        vocab_size=vocab_size,
                        embedding_dim=EMBEDDING_DIM,
                        hidden_size=HIDDEN_DIM,
                        num_classes=num_classes
                    )
                else:
                    print("Using existing model for incremental training...")
            else:
                # Create new model for full training
                print("Creating new model for full training...")
                model = OptimizedSKUNNModel(
                    cat_input_size=X_cat_train.shape[1],
                    vocab_size=vocab_size,
                    embedding_dim=EMBEDDING_DIM,
                    hidden_size=HIDDEN_DIM,
                    num_classes=num_classes
                )

            model = model.to(device)

            # Print model architecture summary
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            print(f"\nEnhanced Model Architecture Summary:")
            print(f"  Embedding Dimension: {EMBEDDING_DIM} (increased for better capacity)")
            print(f"  Hidden Dimension: {HIDDEN_DIM} (increased for better learning)")
            print(f"  Total parameters: {total_params:,}")
            print(f"  Trainable parameters: {trainable_params:,}")
            print(f"  Model size: ~{total_params * 4 / 1024 / 1024:.1f} MB")
            print(f"  Dropout rate: 0.3 (for regularization)")
            print(f"  Bidirectional LSTM: Yes (for better context understanding)")

            # Define loss function and optimizer
            criterion = nn.CrossEntropyLoss()

            # Adjust learning rate for incremental training
            if incremental_mode:
                # Use lower learning rate for incremental training to avoid catastrophic forgetting
                learning_rate = LEARNING_RATE * 0.1  # 10x lower learning rate
                epochs = max(10, EPOCHS // 5)  # Fewer epochs for incremental
                print(f"🔄 Incremental training: LR={learning_rate}, Epochs={epochs}")
            else:
                learning_rate = LEARNING_RATE
                epochs = EPOCHS
                print(f"🚀 Full training: LR={learning_rate}, Epochs={epochs}")

            optimizer = optim.Adam(
                model.parameters(), lr=learning_rate, weight_decay=1e-5)

            # Enhanced learning rate scheduler for better convergence
            scheduler = ReduceLROnPlateau(
                optimizer, mode='min', factor=0.3, patience=5,
                verbose=True, min_lr=1e-6
            )

            # Training loop with early stopping
            mode_text = "Incremental" if incremental_mode else "Full"
            print(f"\n--- Training the Optimized SKU NN Model ({mode_text} Mode) ---")
            print(
                f"Training on {len(train_loader.dataset)} samples, validating on {len(val_loader.dataset)} samples")
            print(
                f"Using device: {device}, batch size: {BATCH_SIZE}, max epochs: {epochs}")

            best_val_loss = float('inf')
            # Enhanced early stopping with accuracy-preserving patience
            patience = 15 if not incremental_mode else 8  # Optimized patience for better efficiency
            patience_counter = 0
            min_improvement = 0.002  # Minimum improvement threshold for early stopping
            training_start_time = time.time()

            # Initialize model path variables
            model_path = ""
            default_model_path = ""

            for epoch in range(epochs):
                epoch_start_time = time.time()

                # Training phase
                model.train()
                train_loss = 0.0
                correct = 0
                total = 0

                for cat_batch, text_batch, labels_batch in train_loader:
                    cat_batch = cat_batch.to(device)
                    text_batch = text_batch.to(device)
                    labels_batch = labels_batch.to(device)

                    # Zero gradients
                    optimizer.zero_grad()

                    # Forward pass
                    outputs = model(cat_batch, text_batch)
                    loss = criterion(outputs, labels_batch)

                    # Backward pass with gradient clipping
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(
                        model.parameters(), max_norm=1.0)
                    optimizer.step()

                    # Track metrics
                    train_loss += loss.item() * cat_batch.size(0)
                    _, predicted = torch.max(outputs, 1)
                    total += labels_batch.size(0)
                    correct += (predicted == labels_batch).sum().item()

                train_loss = train_loss / len(train_loader.dataset)
                train_acc = correct / total

                # Validation phase
                model.eval()
                val_loss = 0.0
                correct = 0
                total = 0

                with torch.no_grad():
                    for cat_batch, text_batch, labels_batch in val_loader:
                        cat_batch = cat_batch.to(device)
                        text_batch = text_batch.to(device)
                        labels_batch = labels_batch.to(device)

                        outputs = model(cat_batch, text_batch)
                        loss = criterion(outputs, labels_batch)

                        val_loss += loss.item() * cat_batch.size(0)
                        _, predicted = torch.max(outputs, 1)
                        total += labels_batch.size(0)
                        correct += (predicted == labels_batch).sum().item()

                val_loss = val_loss / len(val_loader.dataset)
                val_acc = correct / total

                epoch_time = time.time() - epoch_start_time

                # Enhanced progress reporting
                elapsed_time = time.time() - training_start_time
                eta_seconds = (elapsed_time / (epoch + 1)) * (epochs - epoch - 1)
                eta_hours, eta_remainder = divmod(eta_seconds, 3600)
                eta_minutes = eta_remainder // 60

                # Reduced logging frequency - only every 10% or every 10 epochs, whichever is smaller
                log_interval = max(1, min(10, epochs // 10))
                if (epoch + 1) % log_interval == 0 or epoch == 0 or epoch == epochs - 1:
                    print(f"Epoch {epoch+1}/{epochs} [{epoch_time:.1f}s] | "
                          f"Train: {train_acc:.3f} | Val: {(1-val_loss):.3f} | "
                          f"Progress: {((epoch+1)/epochs)*100:.0f}% | "
                          f"ETA: {int(eta_hours)}h{int(eta_minutes)}m")

                # Early stopping with minimum improvement threshold
                if val_loss < (best_val_loss - min_improvement):
                    best_val_loss = val_loss
                    patience_counter = 0
                    # Save the best model with timestamp
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    model_filename = f'sku_nn_model_pytorch_optimized_{timestamp}.pth'
                    model_path = os.path.join(SKU_NN_MODEL_DIR, model_filename)

                    # Also save as the default model name for application use
                    default_model_path = os.path.join(
                        SKU_NN_MODEL_DIR, 'sku_nn_model_pytorch_optimized.pth')

                    # Save both versions
                    torch.save(model.state_dict(), model_path)
                    torch.save(model.state_dict(), default_model_path)
                    print(f"  Saved best model to {model_path}")
                    print(
                        f"  Also saved as default model: {default_model_path}")

                    # Clean up old model checkpoints to save disk space
                    cleanup_old_model_checkpoints(SKU_NN_MODEL_DIR, keep_latest=3)
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        print(
                            f"Early stopping triggered after {epoch+1} epochs")
                        break

                # Step the learning rate scheduler
                scheduler.step(val_loss)

            total_time = time.time() - start_time
            hours, remainder = divmod(total_time, 3600)
            minutes, seconds = divmod(remainder, 60)

            print(f"\n--- SKU NN Model Training Complete (PyTorch) ---")
            print(
                f"Total training time: {int(hours)}h {int(minutes)}m {seconds:.2f}s")
            print(f"Best model saved to {model_path}")
            print(f"Default model path: {default_model_path}")

        else:
            print("\n--- SKU NN Data Preparation Failed, Model Training Skipped ---")
