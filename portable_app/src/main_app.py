# =============================================================================
# PyInstaller Runtime Path Fix
# This must run before any libraries that need bundled data are imported.
# =============================================================================
import sys
import os

# BULLETPROOF spaCy model loading for PyInstaller
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS

    # Define where spaCy should look for its models
    spacy_data_path = os.path.join(application_path)
    spacy_model_path = os.path.join(application_path, 'es_core_news_sm')

    # Set multiple environment variables that spaCy might check
    os.environ['SPACY_DATA'] = spacy_data_path
    os.environ['SPACY_MODEL_PATH'] = spacy_model_path

    # Add the model path to Python's module search path
    # This allows spaCy to find the model as if it were a Python package
    if spacy_model_path not in sys.path:
        sys.path.insert(0, spacy_model_path)
    if spacy_data_path not in sys.path:
        sys.path.insert(0, spacy_data_path)

    # Optional: For debugging, you can print the paths
    print(f"Running in bundled mode. SPACY_DATA set to: {spacy_data_path}")
    print(f"spaCy model path added to sys.path: {spacy_model_path}")
    print(f"Model directory exists: {os.path.exists(spacy_model_path)}")
    if os.path.exists(spacy_model_path):
        print(f"Model directory contents: {os.listdir(spacy_model_path)}")

# =============================================================================
# Regular imports can now begin
# =============================================================================
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox  # For showing error popups
import pandas as pd
# import requests # No longer needed
import sqlite3  # For database connection
from collections import defaultdict  # For counting frequencies
import datetime  # For timestamping Maestro entries
import json  # For loading consolidado
import joblib  # To load trained models
import numpy as np  # For model input reshaping
import re  # For VIN validation
import torch  # For PyTorch

# Performance improvements imports
try:
    import sys
    import os
    # Performance improvements are now in utils
    from utils.performance_improvements.optimizations.database_optimizer import initialize_database_optimization, get_optimizer, get_query_cache
    from utils.performance_improvements.optimizations.parallel_predictor import initialize_parallel_predictor, get_parallel_predictor
    from utils.performance_improvements.enhanced_text_processing.smart_text_processor import initialize_smart_text_processor, get_smart_processor
    from utils.performance_improvements.enhanced_text_processing.equivalencias_analyzer import analyze_equivalencias_from_database

    # New startup optimizations
    from utils.optimized_startup import (
        get_data_loader, get_spacy_loader, get_model_loader,
        get_text_processor, initialize_optimizations
    )
    from utils.optimized_database import get_optimized_database
    from utils.year_range_database import YearRangeDatabaseOptimizer
    from unified_consolidado_processor import get_base_path
    PERFORMANCE_IMPROVEMENTS_AVAILABLE = True
    print("🚀 Performance improvements loaded successfully")
except ImportError as e:
    print(f"⚠️ Performance improvements not available: {e}")
    PERFORMANCE_IMPROVEMENTS_AVAILABLE = False

    # Define fallback get_base_path function
    def get_base_path():
        """Fallback function when unified_consolidado_processor is not available"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            return os.path.dirname(sys.executable)
        else:
            # Running as script
            return os.path.dirname(os.path.abspath(__file__))
# Import our PyTorch model implementation
# Handle PyInstaller bundled imports
def setup_imports():
    """Setup imports for both development and PyInstaller environments."""
    import sys
    import os

    # Check if running in PyInstaller bundle
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            bundle_dir = sys._MEIPASS
            src_path = bundle_dir
        else:
            # Running as frozen executable (not PyInstaller bundle)
            src_path = os.path.dirname(sys.executable)
    else:
        # Running in development
        src_path = os.path.dirname(os.path.abspath(__file__))

    # Add src path to sys.path if not already there
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Also add common subdirectories for PyInstaller
    for subdir in ['models', 'utils', 'core', 'gui']:
        subdir_path = os.path.join(src_path, subdir)
        if os.path.exists(subdir_path) and subdir_path not in sys.path:
            sys.path.insert(0, subdir_path)

# Setup imports
setup_imports()

# Global variables for imports (will be set in try/except blocks)
load_model = None
predict_sku = None
normalize_text = None
DummyTokenizer = None
extract_vin_features_production = None
decode_year = None

# Now import the modules with multiple fallback strategies
try:
    from models.sku_nn_pytorch import load_model, predict_sku
    from utils.text_utils import normalize_text
    from utils.dummy_tokenizer import DummyTokenizer
    from train_vin_predictor import extract_vin_features_production, decode_year
    print("✅ Successfully imported all modules (strategy 1)")
except ImportError as e:
    print(f"Import error (strategy 1): {e}")
    try:
        # Strategy 2: Try importing from current directory
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)

        from models.sku_nn_pytorch import load_model, predict_sku
        from utils.text_utils import normalize_text
        from utils.dummy_tokenizer import DummyTokenizer
        from train_vin_predictor import extract_vin_features_production, decode_year
        print("✅ Successfully imported all modules (strategy 2)")
    except ImportError as e2:
        print(f"Import error (strategy 2): {e2}")
        try:
            # Strategy 3: Try absolute imports
            import models.sku_nn_pytorch as sku_nn
            import utils.text_utils as text_utils
            import utils.dummy_tokenizer as dummy_tokenizer
            import train_vin_predictor as vin_predictor

            load_model = sku_nn.load_model
            predict_sku = sku_nn.predict_sku
            normalize_text = text_utils.normalize_text
            DummyTokenizer = dummy_tokenizer.DummyTokenizer
            extract_vin_features_production = vin_predictor.extract_vin_features_production
            decode_year = vin_predictor.decode_year
            print("✅ Successfully imported all modules (strategy 3)")
        except ImportError as e3:
            print(f"Import error (strategy 3): {e3}")
            # Strategy 4: Import individual files directly
            try:
                import sys
                import os

                # Get the directory where the executable is located
                if getattr(sys, 'frozen', False):
                    base_dir = os.path.dirname(sys.executable)
                else:
                    base_dir = os.path.dirname(os.path.abspath(__file__))

                # Add all possible paths
                possible_paths = [
                    base_dir,
                    os.path.join(base_dir, 'models'),
                    os.path.join(base_dir, 'utils'),
                    os.path.join(base_dir, '..', 'src'),
                    os.path.join(base_dir, '..', 'src', 'models'),
                    os.path.join(base_dir, '..', 'src', 'utils')
                ]

                for path in possible_paths:
                    if os.path.exists(path) and path not in sys.path:
                        sys.path.insert(0, path)

                # Try importing again
                import sku_nn_pytorch
                import text_utils
                import dummy_tokenizer
                import train_vin_predictor

                load_model = sku_nn_pytorch.load_model
                predict_sku = sku_nn_pytorch.predict_sku
                normalize_text = text_utils.normalize_text
                DummyTokenizer = dummy_tokenizer.DummyTokenizer
                extract_vin_features_production = train_vin_predictor.extract_vin_features_production
                decode_year = train_vin_predictor.decode_year
                print("✅ Successfully imported all modules (strategy 4)")
            except ImportError as e4:
                print(f"❌ All import strategies failed. Final error: {e4}")
                print("⚠️ SKU prediction will not work without these modules")
                # Set dummy functions to prevent crashes
                def dummy_load_model(*args, **kwargs):
                    print("❌ load_model not available - imports failed")
                    return None
                def dummy_predict_sku(*args, **kwargs):
                    print("❌ predict_sku not available - imports failed")
                    return "UNKNOWN", 0.0
                def dummy_normalize_text(text):
                    return text.lower() if text else ""
                class DummyTokenizerClass:
                    def __init__(self, *args, **kwargs): pass
                    def transform(self, texts): return [[0] * 30 for _ in texts]
                def dummy_extract_vin(*args, **kwargs):
                    return [0] * 17
                def dummy_decode_year(*args, **kwargs):
                    return 2020

                load_model = dummy_load_model
                predict_sku = dummy_predict_sku
                normalize_text = dummy_normalize_text
                DummyTokenizer = DummyTokenizerClass
                extract_vin_features_production = dummy_extract_vin
                decode_year = dummy_decode_year

import sys

# --- Determine Project Root Path ---
# Get the directory of the current script (src)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Assume the project root is one level up from 'src'
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running as executable
        exe_dir = os.path.dirname(sys.executable)
        resource_path = os.path.join(exe_dir, relative_path)

        print(f"🔍 Looking for resource: {relative_path}")
        print(f"📁 Executable directory: {exe_dir}")
        print(f"📄 Full resource path: {resource_path}")

        # Check if the file exists next to the executable
        if os.path.exists(resource_path):
            print(f"✅ Found resource at executable location: {resource_path}")
            return resource_path
        else:
            print(f"⚠️ Resource not found at executable location: {resource_path}")

            # For database files, always use the path next to executable (even if it doesn't exist)
            # This allows the application to create/access the actual database
            if relative_path.endswith('.db'):
                print(f"📝 Using executable location for database: {resource_path}")
                return resource_path

            # For Excel files, try bundled first, then fall back to executable location
            elif relative_path.endswith('.xlsx'):
                if hasattr(sys, '_MEIPASS'):
                    bundled_path = os.path.join(sys._MEIPASS, relative_path)
                    if os.path.exists(bundled_path):
                        print(f"✅ Using bundled Excel file: {bundled_path}")
                        return bundled_path
                print(f"📝 Using executable location for Excel file: {resource_path}")
                return resource_path

            # For other resources (models, etc.), use bundled resources
            else:
                if hasattr(sys, '_MEIPASS'):
                    fallback_path = os.path.join(sys._MEIPASS, relative_path)
                    print(f"🔄 Using bundled resource: {fallback_path}")
                    return fallback_path
                return resource_path
    else:
        # Running as script - point to client directory structure
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)  # Go up from src/ to project root
        client_dir = os.path.join(project_root, "Fixacar_NUCLEAR_DEPLOYMENT", "Fixacar_SKU_Predictor_CLIENT")
        return os.path.join(client_dir, relative_path)


# --- Configuration (using resource path) ---
DEFAULT_TEXT_PROCESSING_PATH = get_resource_path(os.path.join(
    "Source_Files", "Text_Processing_Rules.xlsx"))
DEFAULT_MAESTRO_PATH = get_resource_path(os.path.join("Source_Files", "Maestro.xlsx"))
DEFAULT_DB_PATH = get_resource_path(os.path.join("Source_Files", "processed_consolidado.db"))
MODEL_DIR = get_resource_path("models")
SKU_NN_MODEL_DIR = os.path.join(MODEL_DIR, "sku_nn")

# Define pattern and count for loading VIN details from chunks (Used by load_vin_details_from_chunks)
# This path might also need adjustment if it's not relative to CWD
# Keeping this relative for now, assuming it's handled elsewhere or CWD is intended for these specific chunks
CONSOLIDADO_CHUNK_PATTERN_FOR_VIN_LOAD = "Consolidado_chunk_{}.json"
NUM_CONSOLIDADO_CHUNKS_FOR_VIN_LOAD = 10


# In-memory data stores
equivalencias_map_global = {}
synonym_expansion_map_global = {}  # New: maps synonyms to equivalence group IDs
abbreviations_map_global = {}  # New: maps abbreviations to full forms
user_corrections_map_global = {}  # New: maps original text to corrected text
series_normalization_map_global = {}  # New: maps (maker, series) to normalized_series
maestro_data_global = []  # This will hold the list of dictionaries
# VIN details lookup is replaced by models

# Loaded Models and Encoders
model_maker = None
encoder_x_maker = None
encoder_y_maker = None
model = None
encoder_x_year = None
encoder_y_year = None
model_series = None
encoder_x_series = None
encoder_y_series = None

# SKU NN Model and Encoders/Tokenizer
sku_nn_model = None
sku_nn_encoder_make = None
sku_nn_encoder_model = None
sku_nn_encoder_series = None
sku_nn_tokenizer_desc = None  # Assuming description is an input
sku_nn_encoder_referencia = None
SKU_NN_MODEL_DIR = os.path.join(MODEL_DIR, "sku_nn")


class FixacarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fixacar SKU Finder v1.0 (with VIN Predictor)")
        self.root.geometry("800x750")  # Increased height

        # Maximize the window on startup to ensure all buttons are visible
        self.root.state('zoomed')  # Windows equivalent of maximized

        # Initialize startup optimizations first
        self.initialize_startup_optimizations()

        # Load initial data and models
        self.load_all_data_and_models()

        # Initialize performance improvements
        self.initialize_performance_optimizations()

        # Setup UI
        self.create_widgets()

    def initialize_startup_optimizations(self):
        """Initialize startup performance optimizations"""
        try:
            print("🚀 Initializing startup optimizations...")

            # Initialize global optimizations
            initialize_optimizations()

            # Start spaCy loading in background
            spacy_loader = get_spacy_loader()
            spacy_loader.start_loading()

            # Initialize optimized database
            self.optimized_db = get_optimized_database()

            # Initialize year range database optimizer
            try:
                db_path = get_resource_path(os.path.join("Source_Files", "processed_consolidado.db"))
                print(f"🔍 Year range optimizer DB path: {db_path}")
                print(f"🔍 DB exists: {os.path.exists(db_path)}")
                self.year_range_optimizer = YearRangeDatabaseOptimizer(db_path)
                print("✅ Year range optimizer initialized successfully")
            except Exception as e:
                print(f"⚠️ Year range optimizer initialization failed: {e}")
                import traceback
                traceback.print_exc()
                self.year_range_optimizer = None

            print("✅ Startup optimizations initialized")

        except Exception as e:
            print(f"⚠️ Startup optimization error: {e}")
            # Continue without optimizations
            self.optimized_db = None
            # Still try to initialize year range optimizer separately
            try:
                db_path = get_resource_path(os.path.join("Source_Files", "processed_consolidado.db"))
                print(f"🔍 Year range optimizer DB path (fallback): {db_path}")
                print(f"🔍 DB exists (fallback): {os.path.exists(db_path)}")
                self.year_range_optimizer = YearRangeDatabaseOptimizer(db_path)
                print("✅ Year range optimizer initialized successfully (fallback)")
            except Exception as e2:
                print(f"⚠️ Year range optimizer fallback initialization failed: {e2}")
                self.year_range_optimizer = None

    def load_all_data_and_models(self):
        """Loads data files and trained prediction models on startup."""
        global equivalencias_map_global, synonym_expansion_map_global, maestro_data_global
        global abbreviations_map_global, user_corrections_map_global
        global model_maker, encoder_x_maker, encoder_y_maker
        global model, encoder_x_year, encoder_y_year
        global model_series, encoder_x_series, encoder_y_series

        print("--- Loading Application Data & Models ---")
        # Load all text processing rules from unified file
        self.load_text_processing_rules(DEFAULT_TEXT_PROCESSING_PATH)
        maestro_data_global = self.load_maestro_data(
            DEFAULT_MAESTRO_PATH, equivalencias_map_global)

        # Load Models
        print("Loading VIN prediction models...")
        try:
            model_maker = joblib.load(os.path.join(
                MODEL_DIR, 'maker_model.joblib'))
            encoder_x_maker = joblib.load(os.path.join(
                MODEL_DIR, 'maker_encoder_x.joblib'))
            encoder_y_maker = joblib.load(os.path.join(
                MODEL_DIR, 'maker_encoder_y.joblib'))
            print("  Maker model loaded.")

            model = joblib.load(os.path.join(
                MODEL_DIR, 'model_model.joblib'))
            encoder_x_year = joblib.load(os.path.join(
                MODEL_DIR, 'model_encoder_x.joblib'))
            encoder_y_year = joblib.load(os.path.join(
                MODEL_DIR, 'model_encoder_y.joblib'))
            print("  Year model loaded.")

            model_series = joblib.load(os.path.join(
                MODEL_DIR, 'series_model.joblib'))
            encoder_x_series = joblib.load(os.path.join(
                MODEL_DIR, 'series_encoder_x.joblib'))
            encoder_y_series = joblib.load(os.path.join(
                MODEL_DIR, 'series_encoder_y.joblib'))
            print("  Series model loaded.")
            print("All models loaded successfully.")

        except FileNotFoundError as e:
            print(
                f"Error loading model file: {e}. VIN prediction will not work.")
            messagebox.showerror(
                "Model Loading Error", f"Could not load model file: {e}\nPlease ensure models are trained and present in the '{MODEL_DIR}' directory.")
            # Set models to None so prediction attempts fail gracefully
            model_maker, model, model_series = None, None, None
        except Exception as e:
            print(f"An unexpected error occurred loading models: {e}")
            messagebox.showerror(
                "Model Loading Error", f"An unexpected error occurred loading models: {e}")
            model_maker, model, model_series = None, None, None

        # Load SKU NN Model and preprocessors
        global sku_nn_model, sku_nn_encoder_make, sku_nn_encoder_model, sku_nn_encoder_series, sku_nn_tokenizer_desc, sku_nn_encoder_referencia
        print("Loading SKU NN model and preprocessors...")
        try:
            # Only load the optimized PyTorch model and encoders
            sku_nn_model_path = os.path.join(
                SKU_NN_MODEL_DIR, 'sku_nn_model_pytorch_optimized.pth')

            sku_nn_encoder_make = joblib.load(os.path.join(
                SKU_NN_MODEL_DIR, 'encoder_maker.joblib'))
            print("  SKU NN Make encoder loaded.")
            sku_nn_encoder_model = joblib.load(os.path.join(
                SKU_NN_MODEL_DIR, 'encoder_model.joblib'))
            print("  SKU NN Model Year encoder loaded.")
            sku_nn_encoder_series = joblib.load(os.path.join(
                SKU_NN_MODEL_DIR, 'encoder_series.joblib'))
            print("  SKU NN Series encoder loaded.")
            try:
                sku_nn_tokenizer_desc = joblib.load(os.path.join(
                    SKU_NN_MODEL_DIR, 'tokenizer.joblib'))
                print("  SKU NN Description tokenizer loaded.")
            except Exception as e:
                print(f"  Error loading tokenizer: {e}")
                try:
                    from utils.pytorch_tokenizer import PyTorchTokenizer
                    sku_nn_tokenizer_desc = PyTorchTokenizer(
                        num_words=10000, oov_token="<OOV>")
                    print("  Using PyTorchTokenizer instead.")
                except ImportError:
                    from utils.dummy_tokenizer import DummyTokenizer
                    sku_nn_tokenizer_desc = DummyTokenizer(
                        num_words=10000, oov_token="<OOV>")
                    print("  Using DummyTokenizer instead.")

            sku_nn_encoder_referencia = joblib.load(os.path.join(
                SKU_NN_MODEL_DIR, 'encoder_referencia.joblib'))
            print("  SKU NN SKU encoder loaded.")

            # Now try to load the optimized PyTorch model
            if os.path.exists(sku_nn_model_path):
                sku_nn_model, _ = load_model(SKU_NN_MODEL_DIR)
                if sku_nn_model:
                    print("  SKU NN Optimized PyTorch model loaded successfully.")
                else:
                    print("  Failed to load SKU NN Optimized PyTorch model.")
            else:
                print(
                    f"  SKU NN Optimized PyTorch model file not found at {sku_nn_model_path}")
                print(
                    "  Note: You need to train and save an optimized PyTorch model first.")
                sku_nn_model = None

        except FileNotFoundError as e:
            print(
                f"Error loading SKU NN model file: {e}. SKU NN prediction will not work.")
            messagebox.showerror("SKU NN Model Error",
                                 f"Could not load SKU NN model file: {e}")
            sku_nn_model = None  # Ensure it's None if loading fails
        except Exception as e:
            print(f"An unexpected error occurred loading SKU NN models: {e}")
            messagebox.showerror(
                "SKU NN Model Error", f"An unexpected error occurred loading SKU NN models: {e}")
            sku_nn_model = None

        # DB connection will be established when needed for search
        print("--- Application Data & Model Loading Complete ---")

    def initialize_performance_optimizations(self):
        """Initialize performance optimization components"""
        if not PERFORMANCE_IMPROVEMENTS_AVAILABLE:
            print("⚠️ Performance improvements not available - running in standard mode")
            return

        print("🚀 Initializing performance optimizations...")

        try:
            # Initialize spaCy text processor
            print("  🧠 Initializing spaCy Spanish text processor...")
            try:
                from utils.spacy_text_processor import initialize_spacy_processor
                self.spacy_processor = initialize_spacy_processor()
                if self.spacy_processor:
                    print("  ✅ spaCy processor initialized successfully")
                else:
                    print("  ⚠️ spaCy processor initialization failed - using legacy processing")
            except Exception as e:
                print(f"  ⚠️ spaCy processor error: {e} - using legacy processing")
                self.spacy_processor = None

            # Cache disabled for stability
            self.referencia_cache = None
            print("  ⚠️ SKU prediction cache disabled for stability")

            # Initialize database optimization
            if os.path.exists(DEFAULT_DB_PATH):
                self.db_optimizer, self.query_cache = initialize_database_optimization(DEFAULT_DB_PATH)

                # Create optimized indexes
                print("  🔧 Creating database indexes...")
                self.db_optimizer.create_optimized_indexes()

                # Analyze performance
                print("  📊 Analyzing database performance...")
                perf_results = self.db_optimizer.analyze_query_performance()

                print("  ✅ Database optimization completed")
            else:
                print(f"  ⚠️ Database not found at {DEFAULT_DB_PATH} - skipping database optimization")
                self.db_optimizer = None
                self.query_cache = None

            # Initialize parallel predictor
            self.parallel_predictor = initialize_parallel_predictor(max_workers=4, enable_early_termination=True)
            print("  ✅ Parallel predictor initialized")

            # Initialize enhanced text processing
            self.smart_processor = initialize_smart_text_processor()
            print("  ✅ Enhanced text processing initialized")

            print("🎯 Performance optimizations ready!")

        except Exception as e:
            print(f"❌ Error initializing performance optimizations: {e}")
            # Set fallback values
            self.referencia_cache = None
            self.db_optimizer = None
            self.query_cache = None
            self.parallel_predictor = None
            self.smart_processor = None

    def enhanced_normalize_text(self, text: str, **kwargs) -> str:
        """
        Enhanced text normalization using spaCy processor when available.
        Priority order:
        1. spaCy processor (NEW - best accuracy for Spanish)
        2. Smart processor (legacy enhanced)
        3. Standard normalize_text (fallback)
        """
        # First try spaCy processor (highest priority)
        if hasattr(self, 'spacy_processor') and self.spacy_processor:
            try:
                # Use spaCy for advanced Spanish linguistic processing
                spacy_result = self.spacy_processor.process_text(text)
                print(f"  🧠 spaCy processing: '{text}' → '{spacy_result}'")
                return spacy_result
            except Exception as e:
                print(f"⚠️ spaCy processing failed: {e}, trying smart processor...")

        # Fallback to smart processor if available
        if PERFORMANCE_IMPROVEMENTS_AVAILABLE and self.smart_processor:
            try:
                # Use enhanced text processing
                from utils.performance_improvements.enhanced_text_processing.smart_text_processor import get_smart_processor
                smart_processor = get_smart_processor()

                # Apply enhanced processing with existing text processor as fallback
                enhanced_text = smart_processor.process_text_enhanced(text, existing_processor=None)

                # Still apply the original normalize_text for compatibility
                final_text = normalize_text(enhanced_text, **kwargs)

                return final_text
            except Exception as e:
                print(f"⚠️ Enhanced text processing failed, using standard: {e}")

        # Final fallback to standard text processing
        return normalize_text(text, **kwargs)

    def expand_synonyms(self, text: str) -> str:
        """
        Global synonym expansion function that preprocesses text by replacing
        industry-specific synonyms with their equivalence group representatives before any prediction method.

        This function ONLY handles Equivalencias.xlsx synonyms (industry-specific terms).
        Linguistic variations (abbreviations, gender, plurals) are handled automatically
        by the normalize_text function.

        This ensures ALL prediction sources (Maestro, Database, Neural Network)
        receive the same normalized input after synonym expansion.
        """
        if not text or not synonym_expansion_map_global:
            return text

        # First normalize text (this handles abbreviations, gender, plurals automatically)
        normalized_text = self.enhanced_normalize_text(text, expand_linguistic_variations=True)
        words = normalized_text.split()
        expanded_words = []

        for word in words:
            # Check if this word has an industry-specific synonym in Equivalencias (CASE-INSENSITIVE)
            word_lower = word.lower()
            if word_lower in synonym_expansion_map_global:
                group_id = synonym_expansion_map_global[word_lower]
                # Use the group_id as a consistent representation
                group_representative = f"GROUP_{group_id}"
                expanded_words.append(group_representative)
                print(f"    Industry synonym: '{word}' -> '{group_representative}' (Group ID: {group_id})")
            else:
                expanded_words.append(word)

        expanded_text = ' '.join(expanded_words)
        return expanded_text

    def normalize_series(self, maker: str, series: str) -> str:
        """
        Normalize series using the series normalization mapping.

        This function implements the hybrid approach:
        1. First check for exact mapping in series_normalization_map_global
        2. If no mapping found, return original series (fallback to fuzzy matching later)

        Args:
            maker: Vehicle maker (e.g., "Mazda", "Ford")
            series: Original series (e.g., "CX30", "CX 30")

        Returns:
            Normalized series (e.g., "CX-30") or original if no mapping found
        """
        if not series or not series_normalization_map_global:
            return series

        # Clean inputs
        maker_clean = maker.upper().strip() if maker else "*"
        series_clean = series.upper().strip()

        # Try maker-specific mapping first
        maker_key = (maker_clean, series_clean)
        if maker_key in series_normalization_map_global:
            normalized = series_normalization_map_global[maker_key]
            print(f"    Series normalized: {maker}/{series} → {normalized} (maker-specific)")
            return normalized

        # Try generic mapping (applies to all makers)
        generic_key = ("*", series_clean)
        if generic_key in series_normalization_map_global:
            normalized = series_normalization_map_global[generic_key]
            print(f"    Series normalized: {maker}/{series} → {normalized} (generic)")
            return normalized

        # No mapping found, return original
        return series

    def calculate_frequency_based_confidence(self, frequency: int, prediction_type: str = "DB") -> float:
        """
        Calculate confidence based on absolute frequency of SKU occurrences in database.

        Updated confidence ranges based on user requirements:
        - 1 occurrence: 30-40% - very low confidence (likely errors)
        - 2-4 occurrences: 40-50% - low confidence
        - 5-9 occurrences: 50-60% - medium-low confidence
        - 10+ occurrences: 80% - high confidence (reduced from 20 to 10)

        Args:
            frequency: Number of times this SKU appears in database for this combination
            prediction_type: Type of prediction for confidence adjustment

        Returns:
            Confidence score between 0.3 and 0.8 (30-80%)
        """
        if frequency == 1:
            # Very low confidence for single occurrences (likely errors)
            base_confidence = 0.30
        elif frequency <= 4:
            # Low confidence for few occurrences
            base_confidence = 0.40 + 0.025 * (frequency - 2)  # 0.40-0.45 range
        elif frequency <= 9:
            # Medium-low confidence
            base_confidence = 0.50 + 0.02 * (frequency - 5)  # 0.50-0.60 range
        else:
            # High confidence for reliable data (10+ occurrences = 80% - reduced from 20)
            base_confidence = 0.80

        # Slight adjustment based on prediction type
        if prediction_type == "DB-Exact":
            multiplier = 1.0  # Full confidence for exact matches
        elif prediction_type.startswith("DB (Unified Fuzzy"):
            multiplier = 0.9  # Slightly lower for fuzzy matches
        elif prediction_type.startswith("DB (3-param"):
            multiplier = 0.8  # Lower for 3-parameter matches
        else:
            multiplier = 0.7  # Lowest for fallback matches

        final_confidence = round(base_confidence * multiplier, 3)

        print(f"    Frequency-based confidence: {frequency} occurrences → {final_confidence} confidence")
        return final_confidence

    def apply_consensus_logic(self, sku_frequency_pairs: list, min_consensus_ratio: float = 0.6) -> list:
        """
        Apply consensus logic to filter out minority/outlier SKUs.

        If we have: 25 × "SKU123", 3 × "SKU456", 1 × "SKU789"
        Only return SKUs that represent significant consensus, not obvious errors.

        Args:
            sku_frequency_pairs: List of (referencia, frequency) tuples
            min_consensus_ratio: Minimum ratio of total occurrences for a SKU to be considered

        Returns:
            Filtered list of (referencia, frequency) tuples with only consensus SKUs
        """
        if not sku_frequency_pairs:
            return []

        total_occurrences = sum(freq for _, freq in sku_frequency_pairs)

        # Sort by frequency (highest first)
        sorted_pairs = sorted(sku_frequency_pairs, key=lambda x: x[1], reverse=True)

        consensus_skus = []
        for referencia, frequency in sorted_pairs:
            ratio = frequency / total_occurrences

            print(f"    Consensus analysis: {referencia} appears {frequency}/{total_occurrences} times ({ratio:.2%})")

            # Include SKUs that meet minimum consensus threshold
            if ratio >= min_consensus_ratio:
                consensus_skus.append((referencia, frequency))
                print(f"      ✅ Included: Strong consensus ({ratio:.2%} ≥ {min_consensus_ratio:.1%})")
            elif frequency >= 10:  # Always include high-frequency SKUs even if ratio is low (reduced from 20 to 10)
                consensus_skus.append((referencia, frequency))
                print(f"      ✅ Included: High frequency ({frequency} ≥ 10 occurrences)")
            else:
                print(f"      ❌ Excluded: Weak consensus ({ratio:.2%} < {min_consensus_ratio:.1%}, freq: {frequency})")

        print(f"    Consensus result: {len(consensus_skus)}/{len(sorted_pairs)} SKUs passed consensus filter")
        return consensus_skus

    def merge_dual_search_results(self, normalized_results: list, original_results: list) -> list:
        """
        Merge and deduplicate results from different text processing approaches on the descripcion column.

        Args:
            normalized_results: List of (referencia, frequency, 'normalized'/'normalized_fuzzy') tuples
            original_results: List of (referencia, frequency, 'original'/'original_fuzzy') tuples

        Returns:
            Merged list of (referencia, frequency) tuples with combined frequencies for duplicate SKUs
        """
        # Dictionary to accumulate frequencies for each SKU
        sku_frequency_map = {}
        sku_sources = {}  # Track which sources found each SKU

        # Process normalized results
        for referencia, frequency, match_type in normalized_results:
            if referencia not in sku_frequency_map:
                sku_frequency_map[referencia] = 0
                sku_sources[referencia] = []
            sku_frequency_map[referencia] += frequency
            sku_sources[referencia].append(f"norm({match_type})")

        # Process original results
        for referencia, frequency, match_type in original_results:
            if referencia not in sku_frequency_map:
                sku_frequency_map[referencia] = 0
                sku_sources[referencia] = []
            sku_frequency_map[referencia] += frequency
            sku_sources[referencia].append(f"orig({match_type})")

        # Convert back to list format and log results
        merged_results = [(referencia, freq) for referencia, freq in sku_frequency_map.items()]

        if merged_results:
            print(f"    📊 Dual search results merged:")
            print(f"      - Normalized matches: {len(normalized_results)}")
            print(f"      - Original matches: {len(original_results)}")
            print(f"      - Total unique SKUs: {len(merged_results)}")

            # Show details for each SKU
            for referencia, freq in sorted(merged_results, key=lambda x: x[1], reverse=True):
                sources = ", ".join(sku_sources[referencia])
                print(f"      - {referencia}: {freq} total frequency (sources: {sources})")
        else:
            print(f"    📊 No matches found in either normalized or original descriptions")

        return merged_results

    def get_most_common_series_for_wmi(self, wmi: str, maker: str) -> str:
        """
        Get the most common series for a given WMI and maker from the database.
        This is used as a fallback when VIN prediction fails.

        Args:
            wmi: World Manufacturer Identifier (first 3 characters of VIN)
            maker: Vehicle manufacturer name

        Returns:
            Most common series name or "Unknown" if not found
        """
        try:
            conn = sqlite3.connect(DEFAULT_DB_PATH)
            cursor = conn.cursor()

            # Get the most common series for this WMI and maker
            cursor.execute("""
                SELECT series, COUNT(*) as frequency
                FROM processed_consolidado
                WHERE SUBSTR(vin_number, 1, 3) = ?
                AND UPPER(maker) = UPPER(?)
                AND series IS NOT NULL
                AND series != ''
                AND series != 'N/A'
                GROUP BY series
                ORDER BY frequency DESC
                LIMIT 1
            """, (wmi, maker))

            result = cursor.fetchone()
            conn.close()

            if result:
                series, frequency = result
                print(f"    📊 Most common series for WMI '{wmi}': '{series}' ({frequency} records)")
                return series
            else:
                print(f"    ❌ No series found for WMI '{wmi}' and maker '{maker}'")
                return "Unknown"

        except Exception as e:
            print(f"    ❌ Error in fallback series lookup: {e}")
            return "Unknown"

    def unified_text_preprocessing(self, text: str) -> str:
        """
        Unified Text Preprocessing Pipeline for ALL text comparisons in the SKU prediction system.

        This ensures that BOTH input descriptions AND target comparison texts (from Database/Maestro)
        receive identical preprocessing, eliminating false penalties for linguistically equivalent terms.

        Pipeline (Priority Order):
        1. User Corrections: Apply learned corrections from user feedback (HIGHEST PRIORITY)
        2. Abbreviations: Expand automotive abbreviations (PUER → PUERTA)
        3. Synonym Expansion: Apply Equivalencias.xlsx industry synonyms
        4. Linguistic Normalization: Handle gender agreement, plurals/singulars
        5. Text Normalization: Convert to lowercase, remove extra spaces, standardize punctuation

        Example:
        - Input: "VIDRIO PUER.DL.D."
        - Step 1: Check user corrections (if user taught: "VIDRIO PUER.DL.D." → "CRISTAL PUERTA DELANTERA DERECHA")
        - Step 2: Apply abbreviations: "PUER" → "PUERTA", "DL" → "DELANTERA", "D" → "DERECHA"
        - Step 3: Apply synonyms: "VIDRIO" → "GROUP_1001" (if in equivalencias)
        - Result: Consistent, learned text processing
        """
        if not text or not text.strip():
            return ""

        # Step 1: Apply user corrections FIRST (highest priority - learned from user feedback)
        corrected_text = self.apply_user_corrections(text)

        # Step 2: Apply abbreviations expansion
        abbreviated_text = self.apply_abbreviations(corrected_text)

        # Step 3: Apply synonym expansion (industry-specific terms from Equivalencias.xlsx)
        expanded_text = self.expand_synonyms(abbreviated_text)

        # Step 4: Apply comprehensive linguistic normalization
        # This handles gender agreement, plurals/singulars
        normalized_text = self.enhanced_normalize_text(expanded_text, expand_linguistic_variations=True)

        # Step 5: Final text normalization (lowercase, spaces, punctuation)
        final_text = normalized_text.lower().strip()

        print(f"    Unified preprocessing: '{text}' → '{final_text}'")
        return final_text

    def apply_user_corrections(self, text: str) -> str:
        """
        Apply user corrections from the User_Corrections tab.
        This has the HIGHEST priority in text processing.
        Applies both phrase-level and intelligent word-level corrections.
        """
        if not text or not user_corrections_map_global:
            return text

        # Step 1: Check for exact phrase match first (highest priority)
        if text in user_corrections_map_global:
            corrected = user_corrections_map_global[text]
            print(f"    ✅ Phrase correction applied: '{text}' → '{corrected}'")
            return corrected

        # Step 2: Apply word-level corrections with context awareness
        corrected_text = self._apply_word_level_corrections(text)
        if corrected_text != text:
            print(f"    ✨ Word-level corrections applied: '{text}' → '{corrected_text}'")
            return corrected_text

        return text

    def _apply_word_level_corrections(self, text: str) -> str:
        """
        Apply context-aware word-level corrections learned from user feedback.
        """
        from utils.text_utils import NOUN_GENDERS

        words = text.split()
        corrected_words = words.copy()

        # Look for word-level correction patterns in the corrections map
        for correction_key, correction_value in user_corrections_map_global.items():
            if correction_key.startswith("WORD: "):
                # Parse the word correction pattern
                word_pattern = self._parse_word_correction_pattern(correction_key, correction_value)
                if word_pattern:
                    # Apply this word correction if context matches
                    corrected_words = self._apply_word_pattern(corrected_words, word_pattern)

        return ' '.join(corrected_words)

    def _parse_word_correction_pattern(self, correction_key: str, correction_value: str) -> dict:
        """
        Parse a word correction pattern from the stored format.
        Example: "WORD: DERECHO → DERECHA (after_feminine_noun)"
        """
        try:
            # Remove "WORD: " prefix
            pattern_part = correction_key[6:]  # Remove "WORD: "

            # Split on " → " to get original and corrected word
            if " → " in pattern_part:
                parts = pattern_part.split(" → ")
                original_word = parts[0].strip()

                # The second part might have context in parentheses
                remaining = parts[1].strip()
                if "(" in remaining and remaining.endswith(")"):
                    # Extract corrected word and context
                    paren_pos = remaining.find("(")
                    corrected_word = remaining[:paren_pos].strip()
                    context_type = remaining[paren_pos+1:-1].strip()  # Remove parentheses
                else:
                    corrected_word = remaining
                    context_type = "unknown"

                return {
                    'original_word': original_word,
                    'corrected_word': correction_value,  # Use the actual correction value
                    'context_type': context_type
                }
        except Exception as e:
            print(f"    ⚠️ Error parsing word pattern '{correction_key}': {e}")

        return None

    def _apply_word_pattern(self, words: list, pattern: dict) -> list:
        """
        Apply a word correction pattern to a list of words if context matches.
        """
        from utils.text_utils import NOUN_GENDERS

        corrected_words = words.copy()
        original_word = pattern['original_word'].lower()
        corrected_word = pattern['corrected_word'].lower()
        context_type = pattern['context_type']

        for i, word in enumerate(words):
            if word.lower() == original_word:
                # Check if context matches
                should_apply = False

                if context_type == "unknown":
                    # Apply without context checking
                    should_apply = True
                elif context_type.startswith("after_") and context_type.endswith("_noun"):
                    # Check for preceding noun with matching gender
                    required_gender = context_type.replace("after_", "").replace("_noun", "")

                    # Look for preceding noun within 3 words
                    for j in range(max(0, i - 3), i):
                        preceding_word = words[j].lower()
                        if preceding_word in NOUN_GENDERS:
                            if NOUN_GENDERS[preceding_word] == required_gender:
                                should_apply = True
                                print(f"    🎯 Context match: '{word}' after {required_gender} noun '{preceding_word}'")
                            break

                if should_apply:
                    # Preserve original case pattern
                    if word.isupper():
                        corrected_words[i] = corrected_word.upper()
                    elif word.istitle():
                        corrected_words[i] = corrected_word.capitalize()
                    else:
                        corrected_words[i] = corrected_word

                    print(f"    🔧 Applied word correction: '{word}' → '{corrected_words[i]}'")

        return corrected_words

    def apply_abbreviations(self, text: str) -> str:
        """
        Apply abbreviations expansion from the Abbreviations tab.
        This replaces the hardcoded AUTOMOTIVE_ABBR dictionary.
        """
        if not text or not abbreviations_map_global:
            return text

        # Split on both spaces and dots to handle cases like "BOC.INF.PUER.DEL.I."
        import re
        words = re.split(r'[\s.]+', text)
        words = [w for w in words if w]  # Remove empty strings
        expanded_words = []

        for word in words:
            # Clean word for lookup (remove punctuation, convert to lowercase)
            clean_word = word.lower().strip('.,;:!?')

            if clean_word in abbreviations_map_global:
                expanded = abbreviations_map_global[clean_word]
                expanded_words.append(expanded)
                print(f"    📝 Abbreviation expanded: '{word}' → '{expanded}'")
            else:
                # Keep original case for non-expanded words
                expanded_words.append(word)


        return ' '.join(expanded_words)

    def save_user_correction(self, original_text: str, corrected_text: str):
        """
        Save a user correction with both phrase-level and intelligent word-level learning.
        This enables context-aware learning that understands gender agreement rules.
        """
        global user_corrections_map_global

        # Update in-memory map for phrase-level corrections
        user_corrections_map_global[original_text] = corrected_text

        # Analyze the correction for word-level learning
        word_level_corrections = self._analyze_correction_for_word_learning(original_text, corrected_text)

        # Update Excel file
        try:
            # Read current data
            file_path = DEFAULT_TEXT_PROCESSING_PATH
            user_corrections_df = pd.read_excel(file_path, sheet_name='User_Corrections')

            # Save phrase-level correction
            existing_mask = user_corrections_df['Original_Text'] == original_text

            if existing_mask.any():
                # Update existing correction (last correction wins)
                user_corrections_df.loc[existing_mask, 'Corrected_Text'] = corrected_text
                user_corrections_df.loc[existing_mask, 'Last_Used'] = pd.Timestamp.now()
                user_corrections_df.loc[existing_mask, 'Usage_Count'] = user_corrections_df.loc[existing_mask, 'Usage_Count'] + 1
                print(f"    📚 Updated existing phrase correction: '{original_text}' → '{corrected_text}'")
            else:
                # Add new phrase correction
                new_row = {
                    'Original_Text': original_text,
                    'Corrected_Text': corrected_text,
                    'Date_Added': pd.Timestamp.now(),
                    'Usage_Count': 1,
                    'Last_Used': pd.Timestamp.now(),
                    'Notes': 'User phrase correction'
                }
                user_corrections_df = pd.concat([user_corrections_df, pd.DataFrame([new_row])], ignore_index=True)
                print(f"    📚 Added new phrase correction: '{original_text}' → '{corrected_text}'")

            # Save word-level corrections
            for word_correction in word_level_corrections:
                user_corrections_df = self._save_word_level_correction(user_corrections_df, word_correction)
                # Also update the in-memory map for word-level corrections
                word_pattern = f"WORD: {word_correction['original_word']} → {word_correction['corrected_word']}"
                context_info = word_correction['context']
                if context_info['type'] != 'unknown':
                    word_pattern += f" ({context_info['type']})"
                user_corrections_map_global[word_pattern] = word_correction['corrected_word']

            # Save back to Excel (preserve other tabs)
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                user_corrections_df.to_excel(writer, sheet_name='User_Corrections', index=False)

        except Exception as e:
            print(f"    ⚠️ Error saving user correction: {e}")

    def _analyze_correction_for_word_learning(self, original_text: str, corrected_text: str) -> list:
        """
        Analyze a user correction to extract intelligent word-level learning patterns.
        Returns a list of context-aware word corrections.
        """
        original_words = original_text.split()
        corrected_words = corrected_text.split()

        word_corrections = []

        # Only process if the texts have the same number of words (simple word substitutions)
        if len(original_words) == len(corrected_words):
            for i, (orig_word, corr_word) in enumerate(zip(original_words, corrected_words)):
                if orig_word != corr_word:
                    # Found a word-level change
                    context = self._analyze_word_context(original_words, i)

                    word_correction = {
                        'original_word': orig_word,
                        'corrected_word': corr_word,
                        'context': context,
                        'position': i,
                        'full_phrase': original_text
                    }
                    word_corrections.append(word_correction)

                    print(f"    🔍 Word-level learning: '{orig_word}' → '{corr_word}' (context: {context['type']})")

        return word_corrections

    def _analyze_word_context(self, words: list, position: int) -> dict:
        """
        Analyze the grammatical context of a word to understand correction patterns.
        """
        from utils.text_utils import NOUN_GENDERS

        context = {
            'type': 'unknown',
            'preceding_noun': None,
            'preceding_noun_gender': None,
            'following_noun': None,
            'following_noun_gender': None
        }

        # Look for preceding nouns (within 3 words)
        for i in range(max(0, position - 3), position):
            word = words[i].lower()
            if word in NOUN_GENDERS:
                context['preceding_noun'] = word
                context['preceding_noun_gender'] = NOUN_GENDERS[word]
                context['type'] = f'after_{NOUN_GENDERS[word]}_noun'
                break

        # Look for following nouns (within 2 words)
        for i in range(position + 1, min(len(words), position + 3)):
            word = words[i].lower()
            if word in NOUN_GENDERS:
                context['following_noun'] = word
                context['following_noun_gender'] = NOUN_GENDERS[word]
                if context['type'] == 'unknown':
                    context['type'] = f'before_{NOUN_GENDERS[word]}_noun'
                break

        return context

    def _save_word_level_correction(self, df: pd.DataFrame, word_correction: dict) -> pd.DataFrame:
        """
        Save a word-level correction to the DataFrame.
        Returns the updated DataFrame.
        """
        # Create a unique identifier for this word correction pattern
        word_pattern = f"WORD: {word_correction['original_word']} → {word_correction['corrected_word']}"
        context_info = word_correction['context']

        if context_info['type'] != 'unknown':
            word_pattern += f" ({context_info['type']})"

        # Check if this word-level correction already exists
        existing_word_mask = df['Original_Text'] == word_pattern

        if existing_word_mask.any():
            # Update existing word correction
            df.loc[existing_word_mask, 'Last_Used'] = pd.Timestamp.now()
            df.loc[existing_word_mask, 'Usage_Count'] = df.loc[existing_word_mask, 'Usage_Count'] + 1
            print(f"    🔄 Updated word-level pattern: {word_pattern}")
        else:
            # Add new word correction
            notes = f"Word-level learning from: '{word_correction['full_phrase']}'"
            if context_info['preceding_noun']:
                notes += f" | Preceding noun: {context_info['preceding_noun']} ({context_info['preceding_noun_gender']})"

            new_word_row = {
                'Original_Text': word_pattern,
                'Corrected_Text': word_correction['corrected_word'],
                'Date_Added': pd.Timestamp.now(),
                'Usage_Count': 1,
                'Last_Used': pd.Timestamp.now(),
                'Notes': notes
            }

            # Add to DataFrame
            new_df = pd.DataFrame([new_word_row])
            df = pd.concat([df, new_df], ignore_index=True)
            print(f"    ✨ Added word-level pattern: {word_pattern}")

        return df

    def open_correction_dialog(self, original_desc: str, display_desc: str):
        """
        Open a dialog for the user to correct the text processing result.
        This enables the learning mechanism for text processing.
        """
        # Create correction dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Correct Description")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Correct Description Processing",
            font=("", 12, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Original text
        ttk.Label(main_frame, text="Original text you entered:", font=("", 10, "bold")).pack(anchor="w")
        original_label = ttk.Label(
            main_frame,
            text=original_desc,
            font=("", 10),
            foreground="blue",
            wraplength=450
        )
        original_label.pack(anchor="w", pady=(0, 10))

        # Current processed result
        ttk.Label(main_frame, text="Current processed result:", font=("", 10, "bold")).pack(anchor="w")
        current_label = ttk.Label(
            main_frame,
            text=display_desc,
            font=("", 10),
            foreground="red",
            wraplength=450
        )
        current_label.pack(anchor="w", pady=(0, 10))

        # Correction input
        ttk.Label(main_frame, text="Enter the correct description:", font=("", 10, "bold")).pack(anchor="w")
        correction_var = tk.StringVar(value=display_desc)
        correction_entry = ttk.Entry(main_frame, textvariable=correction_var, width=60)
        correction_entry.pack(fill="x", pady=(5, 15))
        correction_entry.focus()
        correction_entry.select_range(0, tk.END)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x")

        def save_correction():
            corrected_text = correction_var.get().strip()
            if corrected_text and corrected_text != display_desc:
                # Save the correction (map from ORIGINAL text to corrected text)
                # This ensures the correction is found during processing pipeline
                self.save_user_correction(original_desc, corrected_text)

                # Reload text processing rules to include the new correction
                self.load_text_processing_rules(DEFAULT_TEXT_PROCESSING_PATH)

                # Re-process only the SKU search with the new correction (don't clear VIN details)
                self._rerun_sku_search_after_correction()

                # Show success message
                messagebox.showinfo(
                    "Correction Saved",
                    f"✅ Correction saved successfully!\n\n"
                    f"The system has learned that:\n"
                    f"'{display_desc}' → '{corrected_text}'\n\n"
                    f"Search results have been updated."
                )
            dialog.destroy()

        def cancel_correction():
            dialog.destroy()

        # Cancel button
        cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=cancel_correction)
        cancel_btn.pack(side="right", padx=(5, 0))

        # Save button
        save_btn = ttk.Button(buttons_frame, text="Save Correction", command=save_correction)
        save_btn.pack(side="right")

        # Bind Enter key to save
        dialog.bind('<Return>', lambda e: save_correction())
        dialog.bind('<Escape>', lambda e: cancel_correction())

    def _rerun_sku_search_after_correction(self):
        """
        Re-run SKU search after text correction without clearing VIN details.
        This preserves the existing vehicle details and only updates SKU predictions.
        """
        print("\n--- Re-running SKU search after text correction ---")

        # Check if we have vehicle details from previous VIN prediction
        if not hasattr(self, 'vehicle_details') or not self.vehicle_details:
            print("No vehicle details available. Running full search instead.")
            self.find_skus_handler()
            return

        # Clear only the SKU results area, not the vehicle details
        self._clear_results_area()

        # Re-process parts with the corrected text and existing vehicle details
        self._process_parts_and_continue_search()

    def create_abbreviated_version(self, descripcion: str) -> str:
        """
        Create abbreviated version of description to match database format.
        Database uses heavily abbreviated forms like 'paragolpes del' instead of 'paragolpes delantero'.

        Based on database analysis, common patterns are:
        - 'paragolpes del' (25 records)
        - 'farola d' (18 records)
        - 'farola i' (15 records)
        - 'guardafango deld' (13 records)
        - 'absorbimpacto del' (11 records)
        """
        desc = descripcion.lower()

        # Apply specific transformations based on database patterns
        # Handle compound terms first
        if 'absorbedor de impactos' in desc:
            desc = desc.replace('absorbedor de impactos', 'absorbimpacto')

        if 'electroventilador' in desc:
            desc = desc.replace('electroventilador', 'electrovent')

        # Handle luz -> farola transformation for lights
        if 'luz antiniebla' in desc:
            desc = desc.replace('luz antiniebla', 'farola')
        elif 'luz' in desc:
            desc = desc.replace('luz', 'farola')

        # Common abbreviations found in database
        abbreviations = {
            'delantero': 'del',
            'delantera': 'del',
            'trasero': 'tra',
            'trasera': 'tra',
            'izquierdo': 'i',
            'izquierda': 'i',
            'derecho': 'd',
            'derecha': 'd',
            'superior': 'sup',
            'inferior': 'inf',
            'anterior': 'ant',
            'posterior': 'post'
        }

        # Apply abbreviations
        for full_form, abbrev in abbreviations.items():
            desc = desc.replace(full_form, abbrev)

        # Remove common words that might not be in database (CASE-INSENSITIVE)
        remove_words = ['de', 'la', 'el', 'los', 'las', 'antiniebla']
        words = desc.split()
        words = [w for w in words if w.lower() not in remove_words]

        return ' '.join(words)

    def _calculate_description_similarity(self, query_desc: str, db_desc: str) -> float:
        """
        Calculate similarity between query description and database description.
        Handles gender variations, abbreviations, and partial matches.

        Examples:
        - 'farola derecho' vs 'farola derecha' → high similarity (gender variation)
        - 'farola der' vs 'farola derecha' → high similarity (abbreviation)
        - 'farola dere' vs 'farola derecha' → high similarity (partial)

        CASE-INSENSITIVE: All comparisons are done in lowercase.
        """
        if not query_desc or not db_desc:
            return 0.0

        # Convert to lowercase for case-insensitive comparison
        query_desc = query_desc.lower()
        db_desc = db_desc.lower()

        # Exact match
        if query_desc == db_desc:
            return 1.0

        # Split into words for detailed comparison
        query_words = query_desc.split()
        db_words = db_desc.split()

        # If different number of words, use sequence matching
        if len(query_words) != len(db_words):
            from difflib import SequenceMatcher
            return SequenceMatcher(None, query_desc, db_desc).ratio()

        # Word-by-word comparison with special handling
        word_similarities = []
        for q_word, db_word in zip(query_words, db_words):
            word_sim = self._calculate_word_similarity(q_word, db_word)
            word_similarities.append(word_sim)

        # Average similarity across all words
        return sum(word_similarities) / len(word_similarities) if word_similarities else 0.0

    def _calculate_word_similarity(self, word1: str, word2: str) -> float:
        """
        Calculate similarity between two words with special handling for:
        - Gender variations (derecho/derecha)
        - Abbreviations (der/derecha, izq/izquierda)
        - Partial matches (dere/derecha)
        - Plurals and singulars (farola/farolas, paragolpe/paragolpes)

        CASE-INSENSITIVE: All comparisons are done in lowercase.
        """
        if not word1 or not word2:
            return 0.0

        # Convert to lowercase for case-insensitive comparison
        word1 = word1.lower()
        word2 = word2.lower()

        # Exact match
        if word1 == word2:
            return 1.0

        # Import the gender variant checker
        from utils.text_utils import are_gender_variants

        # Check for exact gender variants first (highest priority)
        if are_gender_variants(word1, word2):
            return 1.0  # Perfect match for gender variants

        # Handle common abbreviations and their full forms
        abbreviation_map = {
            'der': ['derecho', 'derecha'],
            'izq': ['izquierdo', 'izquierda'],
            'iz': ['izquierdo', 'izquierda'],
            'i': ['izquierdo', 'izquierda'],
            'del': ['delantero', 'delantera'],
            'delan': ['delantero', 'delantera'],
            'tra': ['trasero', 'trasera'],
            'tras': ['trasero', 'trasera'],
            't': ['trasero', 'trasera'],  # Single letter abbreviation
            'd': ['derecho', 'derecha', 'delantero', 'delantera'],  # Ambiguous - could be either
            'ant': ['anterior'],
            'post': ['posterior'],
            'sup': ['superior'],
            'inf': ['inferior'],
        }

        # Check if one word is an abbreviation of the other
        for abbrev, full_forms in abbreviation_map.items():
            if word1 == abbrev and word2 in full_forms:
                return 0.95  # High similarity for known abbreviations
            if word2 == abbrev and word1 in full_forms:
                return 0.95

        # Handle gender variations with pattern matching (fallback for unknown words)
        if len(word1) > 2 and len(word2) > 2:
            # Check if words are identical except for last character (gender)
            if word1[:-1] == word2[:-1] and word1[-1] in 'oa' and word2[-1] in 'oa':
                return 0.95  # High similarity for gender variations

        # Handle plurals and singulars
        plural_similarity = self._check_plural_singular_similarity(word1, word2)
        if plural_similarity > 0:
            return plural_similarity

        # Handle partial matches (one word is a prefix of the other)
        if word1.startswith(word2) or word2.startswith(word1):
            shorter = min(word1, word2, key=len)
            longer = max(word1, word2, key=len)
            if len(shorter) >= 3:  # Minimum 3 characters for partial match
                return 0.8 + 0.1 * (len(shorter) / len(longer))

        # Use sequence matching for other cases
        from difflib import SequenceMatcher
        return SequenceMatcher(None, word1, word2).ratio()

    def _check_plural_singular_similarity(self, word1: str, word2: str) -> float:
        """
        Check if two words are plural/singular variations of each other.
        Spanish plural rules:
        - Add 's' to words ending in vowel: farola → farolas
        - Add 'es' to words ending in consonant: paragolpe → paragolpes
        - Some irregular plurals
        """
        if len(word1) < 3 or len(word2) < 3:
            return 0.0

        # Check if one is plural of the other
        longer = max(word1, word2, key=len)
        shorter = min(word1, word2, key=len)

        # Rule 1: Add 's' (farola → farolas)
        if longer == shorter + 's':
            return 0.92

        # Rule 2: Add 'es' (paragolpe → paragolpes)
        if longer == shorter + 'es':
            return 0.92

        # Rule 3: Some words change ending (e.g., luz → luces)
        # Check if removing 'es' and adding common singular endings works
        if longer.endswith('es') and len(longer) > 3:
            stem = longer[:-2]  # Remove 'es'
            # Try common singular endings
            singular_candidates = [stem, stem + 'z', stem + 'x']
            if shorter in singular_candidates:
                return 0.92

        # Rule 4: Words ending in 'z' become 'ces' (luz → luces)
        if longer.endswith('ces') and shorter.endswith('z'):
            if longer[:-3] == shorter[:-1]:  # Compare stems
                return 0.92

        return 0.0

    def load_text_processing_rules(self, file_path: str):
        """
        Load all text processing rules from the unified Text_Processing_Rules.xlsx file.
        This includes equivalencias, abbreviations, user corrections, and series normalization.
        Uses optimized loading with caching when available.
        """
        global equivalencias_map_global, synonym_expansion_map_global
        global abbreviations_map_global, user_corrections_map_global, series_normalization_map_global

        print(f"Loading text processing rules from: {file_path}")
        if not os.path.exists(file_path):
            print(f"Warning: Text processing rules file not found at {file_path}. Text processing will be limited.")
            return

        try:
            # Try optimized loading first
            if hasattr(self, 'optimized_db') and self.optimized_db:
                try:
                    data_loader = get_data_loader()
                    optimized_rules = data_loader.load_text_processing_rules_optimized(file_path)

                    # Convert optimized format to global variables
                    equivalencias_map_global = optimized_rules.get('equivalencias', {})
                    abbreviations_map_global = optimized_rules.get('abbreviations', {})
                    user_corrections_map_global = optimized_rules.get('user_corrections', {})
                    series_normalization_map_global = optimized_rules.get('series_normalization', {})

                    # Create synonym expansion map for equivalencias
                    synonym_expansion_map_global = {}
                    for i, (term, equiv) in enumerate(equivalencias_map_global.items(), 1):
                        synonym_expansion_map_global[term] = i

                    print(f"✅ Loaded text processing rules (optimized):")
                    print(f"   - Equivalencias: {len(equivalencias_map_global)} mappings")
                    print(f"   - Abbreviations: {len(abbreviations_map_global)} mappings")
                    print(f"   - User Corrections: {len(user_corrections_map_global)} mappings")
                    print(f"   - Series Normalization: {len(series_normalization_map_global)} mappings")
                    return

                except Exception as e:
                    print(f"⚠️ Optimized loading failed: {e}, falling back to standard loading")

            # Fallback to standard loading
            # Load Equivalencias tab
            equivalencias_df = pd.read_excel(file_path, sheet_name='Equivalencias')
            equivalencias_map_global = self._process_equivalencias_data(equivalencias_df)

            # Load Abbreviations tab
            abbreviations_df = pd.read_excel(file_path, sheet_name='Abbreviations')
            abbreviations_map_global = self._process_abbreviations_data(abbreviations_df)

            # Load User Corrections tab
            user_corrections_df = pd.read_excel(file_path, sheet_name='User_Corrections')
            user_corrections_map_global = self._process_user_corrections_data(user_corrections_df)

            # Load Series Normalization tab
            try:
                series_df = pd.read_excel(file_path, sheet_name='Series')
                series_normalization_map_global = self._process_series_normalization_data(series_df)
            except Exception as e:
                print(f"Warning: Could not load Series tab: {e}. Series normalization will be disabled.")
                series_normalization_map_global = {}

            print(f"✅ Loaded text processing rules:")
            print(f"   - Equivalencias: {len(equivalencias_map_global)} mappings")
            print(f"   - Abbreviations: {len(abbreviations_map_global)} mappings")
            print(f"   - User Corrections: {len(user_corrections_map_global)} mappings")
            print(f"   - Series Normalization: {len(series_normalization_map_global)} mappings")



        except Exception as e:
            print(f"Error loading text processing rules: {e}")
            # Initialize empty maps as fallback
            equivalencias_map_global = {}
            synonym_expansion_map_global = {}
            abbreviations_map_global = {}
            user_corrections_map_global = {}
            series_normalization_map_global = {}

    def _process_equivalencias_data(self, df: pd.DataFrame) -> dict:
        """Process equivalencias data and create both ID mapping and synonym expansion dictionary."""
        equivalencias_map = {}
        synonym_expansion_map = {}

        for index, row in df.iterrows():
            equivalencia_row_id = index + 1  # 1-based ID

            # Process all non-empty cells in the row as synonyms
            synonyms = []
            for col in df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    synonym = str(row[col]).strip()
                    synonyms.append(synonym)

            # Create mappings for each synonym
            for synonym in synonyms:
                from utils.text_utils import normalize_text
                normalized_synonym = normalize_text(synonym)
                equivalencias_map[normalized_synonym] = equivalencia_row_id
                synonym_expansion_map[normalized_synonym] = equivalencia_row_id

        # Store the synonym expansion map globally
        global synonym_expansion_map_global
        synonym_expansion_map_global = synonym_expansion_map

        return equivalencias_map

    def _process_abbreviations_data(self, df: pd.DataFrame) -> dict:
        """Process abbreviations data into a mapping dictionary using canonical structure."""
        abbreviations_map = {}

        # Process each row as a canonical group (like equivalencias)
        for index, row in df.iterrows():
            # Get all non-empty cells in the row
            canonical_group = []
            for col in df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    term = str(row[col]).strip().lower()
                    canonical_group.append(term)

            if len(canonical_group) >= 2:  # Need at least canonical form + 1 abbreviation
                canonical_form = canonical_group[0]  # First column is the canonical form
                abbreviations = canonical_group[1:]  # Rest are abbreviations

                # Map all abbreviations to the canonical form
                for abbr in abbreviations:
                    abbreviations_map[abbr] = canonical_form

                print(f"    Abbreviation group: {canonical_form} ← {', '.join(abbreviations)}")

        return abbreviations_map

    def _process_user_corrections_data(self, df: pd.DataFrame) -> dict:
        """Process user corrections data into a mapping dictionary for both phrase and word-level corrections."""
        corrections_map = {}

        if 'Original_Text' in df.columns and 'Corrected_Text' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row['Original_Text']) and pd.notna(row['Corrected_Text']):
                    original = str(row['Original_Text']).strip()
                    corrected = str(row['Corrected_Text']).strip()
                    corrections_map[original] = corrected

                    # Log the type of correction being loaded
                    if original.startswith("WORD: "):
                        print(f"    🔧 Loaded word-level pattern: {original}")
                    else:
                        print(f"    📝 Loaded phrase correction: {original} → {corrected}")

        return corrections_map

    def _process_series_normalization_data(self, df: pd.DataFrame) -> dict:
        """
        Process series normalization data into a mapping dictionary.

        Expected format: Each row contains series variations that should be normalized to the first column.
        Example: CX-30 | CX30 | CX 30 | MAZDA/CX-30 (DM)/BASICO

        Returns:
            dict: Mapping of (maker, original_series) -> normalized_series
        """
        series_map = {}

        for index, row in df.iterrows():
            # Get all non-empty values from the row
            series_variations = []
            for col in df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    series_variations.append(str(row[col]).strip())

            if len(series_variations) < 2:
                continue  # Need at least 2 variations to create mappings

            # First variation is the canonical/normalized form
            normalized_series = series_variations[0]

            # Extract maker from the normalized form if it contains maker info
            # Example: "MAZDA/CX-30 (DM)/BASICO" -> maker="MAZDA", series="CX-30"
            if '/' in normalized_series:
                parts = normalized_series.split('/')
                if len(parts) >= 2:
                    maker = parts[0].strip()
                    series_part = parts[1].strip()
                    # Remove parenthetical info: "CX-30 (DM)" -> "CX-30"
                    if '(' in series_part:
                        series_part = series_part.split('(')[0].strip()
                    normalized_series = series_part
                else:
                    # Fallback: use the whole string and assume no specific maker
                    maker = None
            else:
                # Simple series without maker info
                maker = None

            # Create mappings for all variations
            for variation in series_variations:
                if variation != normalized_series:  # Don't map to itself
                    # Clean the variation (remove maker prefix if present)
                    clean_variation = variation
                    if '/' in variation:
                        parts = variation.split('/')
                        if len(parts) >= 2:
                            clean_variation = parts[1].strip()
                            if '(' in clean_variation:
                                clean_variation = clean_variation.split('(')[0].strip()

                    # Create mapping key
                    if maker:
                        # Maker-specific mapping
                        key = (maker.upper(), clean_variation.upper())
                        series_map[key] = normalized_series
                        print(f"    Series mapping: {maker}/{clean_variation} → {normalized_series}")
                    else:
                        # Generic mapping (applies to all makers)
                        key = ("*", clean_variation.upper())
                        series_map[key] = normalized_series
                        print(f"    Series mapping: */{clean_variation} → {normalized_series}")

        print(f"Loaded {len(series_map)} series normalization mappings")
        return series_map

    def load_equivalencias_data(self, file_path: str) -> dict:
        """
        Load equivalencias data and create both ID mapping and synonym expansion dictionary.
        Returns the ID mapping (for backward compatibility).
        """
        print(f"Loading equivalencias from: {file_path}")
        if not os.path.exists(file_path):
            print(
                f"Warning: Equivalencias file not found at {file_path}. Equivalency linking will be disabled.")
            return {}
        try:
            df = pd.read_excel(file_path, sheet_name=0)
            equivalencias_map = {}
            synonym_expansion_map = {}  # New: maps synonyms to equivalence group IDs

            for index, row in df.iterrows():
                equivalencia_row_id = index + 1
                row_terms = []  # Collect all terms in this row

                # First pass: collect all normalized terms in this row
                for col_name in df.columns:
                    term = row[col_name]
                    if pd.notna(term) and str(term).strip():
                        normalized_term = normalize_text(str(term))
                        if normalized_term:
                            row_terms.append(normalized_term)
                            # Store with lowercase key for case-insensitive lookup
                            equivalencias_map[normalized_term.lower()] = equivalencia_row_id

                # Second pass: create synonym mappings (all terms map to the equivalence group ID)
                # Ensure case-insensitive storage by using lowercase keys
                if row_terms:
                    # All terms in this row belong to the same equivalence group
                    for term in row_terms:
                        synonym_expansion_map[term.lower()] = equivalencia_row_id

            # Store the synonym expansion map globally for use in preprocessing
            global synonym_expansion_map_global
            synonym_expansion_map_global = synonym_expansion_map

            print(f"Loaded {len(equivalencias_map)} normalized term mappings from {len(df)} rows in Equivalencias.")
            print(f"Created {len(synonym_expansion_map)} synonym expansion mappings.")
            return equivalencias_map
        except Exception as e:
            print(
                f"Error loading or processing Equivalencias.xlsx: {e}. Equivalency linking will be disabled.")
            return {}

    def load_maestro_data(self, file_path: str, equivalencias_map: dict) -> list:
        # (Content remains the same as before)
        print(f"Loading maestro data from: {file_path}")
        # Updated column list - using original consolidado field names
        maestro_columns = [
            'Maestro_ID', 'maker', 'model',
            'series', 'Original_descripcion_Input', 'Normalized_descripcion_Input', 'Confirmed_referencia',
            'Source', 'Date_Added'
        ]
        data_dir = os.path.dirname(file_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(file_path):
            print(
                f"Maestro file not found at {file_path}. Creating a new one with headers.")
            df_maestro = pd.DataFrame(columns=maestro_columns)
            try:
                df_maestro.to_excel(file_path, index=False)
                return []
            except Exception as e:
                print(
                    f"Error creating Maestro.xlsx: {e}. Maestro data will be empty.")
                return []
        try:
            df_maestro = pd.read_excel(file_path, sheet_name=0)
            if 'Maestro_ID' in df_maestro.columns:
                df_maestro['Maestro_ID'] = pd.to_numeric(
                    df_maestro['Maestro_ID'], errors='coerce').fillna(0).astype(int)
            if df_maestro.empty:
                print("Maestro file is empty.")
                return []
            maestro_list = []
            for _, row in df_maestro.iterrows():
                entry = row.to_dict()

                # Fix bracketed values in text columns
                for col in ['maker', 'series']:
                    if col in entry and pd.notna(entry[col]):
                        value_str = str(entry[col]).strip()
                        if value_str.startswith("['") and value_str.endswith("']"):
                            entry[col] = value_str[2:-2]  # Remove [''] format
                        elif value_str.startswith('[') and value_str.endswith(']'):
                            entry[col] = value_str[1:-1].strip("'\"")  # Remove [] format

                # Handle both old and new column names for backward compatibility
                original_desc = entry.get('Original_descripcion_Input', entry.get('descripcion', ""))
                normalized_desc = entry.get('Normalized_descripcion_Input', "")

                if pd.notna(original_desc):
                    # Store original description in 'descripcion' and normalized in 'normalized_descripcion'
                    entry['descripcion'] = str(original_desc)
                    if pd.notna(normalized_desc) and str(normalized_desc).strip():
                        entry['normalized_descripcion'] = str(normalized_desc)
                    else:
                        # If no normalized version, create one
                        entry['normalized_descripcion'] = normalize_text(str(original_desc))
                else:
                    entry['descripcion'] = ""
                    entry['normalized_descripcion'] = ""

                # Fix bracketed values in integer columns
                for col in ['Maestro_ID', 'model']:
                    if col in entry and pd.notna(entry[col]):
                        original_value = entry[col]  # Store original value
                        try:
                            value_str = str(entry[col]).strip()
                            if value_str.startswith('[') and value_str.endswith(']'):
                                value_str = value_str[1:-1].strip("'\"")  # Remove [2012] -> 2012
                            entry[col] = int(value_str)
                        except (ValueError, TypeError):
                            # Keep original value if conversion fails, don't set to None
                            print(f"Warning: Could not convert {col} value '{original_value}' to integer, keeping original value")
                            entry[col] = original_value

                # Handle referencia field with new column name
                referencia_value = entry.get('Confirmed_referencia', entry.get('referencia', ""))
                if pd.notna(referencia_value):
                    entry['referencia'] = str(referencia_value)
                else:
                    entry['referencia'] = ""

                # Removed Confidence column processing - confidence is calculated dynamically
                maestro_list.append(entry)
            print(f"Loaded {len(maestro_list)} records from Maestro.xlsx.")
            return maestro_list
        except Exception as e:
            print(
                f"Error loading or processing Maestro.xlsx: {e}. Maestro data will be empty.")
            return []

    # Removed load_vin_details_from_chunks

    def create_widgets(self):
        """Creates the GUI widgets."""
        # --- Top Frame with two columns ---
        top_frame = ttk.Frame(self.root, padding=(10, 5))
        top_frame.pack(padx=10, pady=10, fill="x", expand=False)

        # Configure columns for 60/40 split
        top_frame.columnconfigure(0, weight=60)  # Left column (60%)
        top_frame.columnconfigure(1, weight=40)  # Right column (40%)

        # --- Input Frame (Left Column) ---
        input_frame = ttk.LabelFrame(top_frame, text="Input", padding=(10, 5))
        input_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")

        # VIN Input
        ttk.Label(input_frame, text="VIN (17 characters):").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        self.vin_entry = ttk.Entry(input_frame, width=25)
        self.vin_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Part Descriptions Input
        # Create a frame to hold the label and the instruction text
        part_desc_label_frame = ttk.Frame(input_frame)
        part_desc_label_frame.grid(
            row=1, column=0, padx=5, pady=5, sticky="nw")

        # Main label
        ttk.Label(part_desc_label_frame, text="Part Descriptions").grid(
            row=0, column=0, sticky="nw")

        # Instruction text below the main label
        ttk.Label(part_desc_label_frame, text="(one per line)", font=("", 8)).grid(
            row=1, column=0, sticky="nw")

        # Text input field - now spans across columns 1 and 2 to continue under the Find SKUs button
        self.parts_text = tk.Text(
            input_frame, width=40, height=5)  # Reduced width
        self.parts_text.grid(row=1, column=1, padx=5,
                             pady=5, sticky="ew", columnspan=2)
        input_frame.columnconfigure(1, weight=1)  # Allow parts_text to expand

        # Create a custom style for buttons with better contrast
        self.style = ttk.Style()
        self.style.configure("Accent.TButton",
                             background="#333333",  # Dark gray background
                             foreground="#ffffff",  # White text
                             font=("", 10, "bold"))  # Bold font

        # Add a style for the manual entry confirm button
        self.style.configure("Manual.TButton",
                             background="#333333",  # Dark gray background
                             foreground="#ffffff",  # White text
                             font=("", 9, "bold"))  # Bold font

        # Create a custom button class that uses a dark background with white text
        class DarkButton(tk.Button):
            def __init__(self, master=None, **kwargs):
                super().__init__(master, **kwargs)
                self.configure(
                    background="#333333",  # Dark gray background
                    foreground="#ffffff",  # White text
                    font=("", 10, "bold"),  # Bold font
                    borderwidth=1,
                    relief=tk.RAISED,
                    padx=10,
                    pady=5,
                    activebackground="#555555",  # Slightly lighter when clicked
                    activeforeground="#ffffff",  # White text when active
                    disabledforeground="#ffffff"  # White text when disabled
                )

        # Find SKUs Button - moved to the position indicated by the red arrow (between VIN and Part Descriptions)
        self.find_button = DarkButton(
            input_frame, text="Find SKUs",
            command=self.find_skus_handler)
        self.find_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # --- Vehicle Details Frame (Right Column) ---
        self.vehicle_details_frame = ttk.LabelFrame(
            top_frame, text="Predicted Vehicle Details", padding=(10, 5))
        self.vehicle_details_frame.grid(
            row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")

        # Placeholder for vehicle details (will be populated after prediction)
        self.vehicle_details_placeholder = ttk.Label(
            self.vehicle_details_frame, text="Vehicle details will appear here after VIN prediction.")
        self.vehicle_details_placeholder.pack(padx=5, pady=5, anchor="nw")

        # --- Output Frame ---
        output_frame = ttk.LabelFrame(
            # Changed title to be more specific
            self.root, text="SKU Suggestions", padding=(10, 5))
        output_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Make the output frame resize correctly
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        # Scrollable Canvas for results
        canvas = tk.Canvas(output_frame)
        scrollbar = ttk.Scrollbar(
            output_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        # Configure the scrollable frame to expand to fill the canvas width
        self.scrollable_frame.columnconfigure(0, weight=1)

        # Bind the frame to update the scrollregion when its size changes
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Create window with scrollable frame and configure it to expand horizontally
        canvas.create_window((0, 0), window=self.scrollable_frame,
                             anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        # Make sure the canvas expands to fill the frame
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Update the canvas when it's resized to adjust the scrollable frame width
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)

        # Placeholder Label inside scrollable frame
        self.results_placeholder_label = ttk.Label(
            self.scrollable_frame, text="Enter VIN and Descriptions, then click 'Find SKUs'.")
        self.results_placeholder_label.pack(padx=5, pady=5, anchor="nw")

        # --- Bottom Frame for Save Button ---
        bottom_frame = ttk.Frame(self.root, padding=(10, 5))
        bottom_frame.pack(side=tk.BOTTOM, fill="x",
                          expand=False, pady=(0, 10), padx=10)

        self.save_button = DarkButton(
            bottom_frame, text="Save Confirmed Selections",
            command=self.save_selections_handler,
            state=tk.DISABLED)
        # Pack inside the bottom_frame with some padding
        self.save_button.pack(pady=5)

        # Instance variables
        self.vehicle_details = None
        self.processed_parts = None
        self.current_suggestions = {}
        self.selection_vars = {}
        self.part_frames_widgets = []  # To store part_frame widgets for responsive layout
        self.current_num_columns = 0  # To track current number of columns in results

        # Removed manual input variables

    def _correct_vin(self, vin: str) -> str:
        """
        Corrects common VIN input mistakes:
        - Replaces I/i with 1
        - Replaces O/o/Q/q with 0
        Returns the corrected VIN string.
        """
        return vin.upper().replace('I', '1').replace('O', '0').replace('Q', '0')

    def _format_confidence_percentage(self, confidence: float) -> str:
        """
        Converts confidence score to percentage format for display.

        Args:
            confidence: Confidence score (0.0-1.0)

        Returns:
            Formatted percentage string (e.g., "75%")
        """
        return f"{int(confidence * 100)}%"

    def _shorten_source_name(self, source_name: str) -> str:
        """
        Shortens source names for better UI display while preserving key information.

        Args:
            source_name: Original source name from prediction

        Returns:
            Shortened source name for UI display
        """
        if not source_name:
            return ""

        # Handle multiple sources (comma-separated)
        if ", " in source_name:
            sources = source_name.split(", ")
            shortened_sources = [self._shorten_source_name(s.strip()) for s in sources]
            return ", ".join(shortened_sources)

        # Shorten individual source names
        source = source_name.strip()

        # Maestro sources
        if source == "Maestro":
            return "Maestro"

        # Neural Network sources
        if source == "SKU-NN" or "Neural" in source:
            return "SKU-NN"

        # Database sources - return full descriptions to see matching methods
        if source.startswith("DB"):
            return source  # Return full description

        # Fallback for any other sources
        return source[:15] + "..." if len(source) > 15 else source

    def _get_sku_nn_prediction(self, maker: str, model: str, series: str, descripcion: str) -> str | None:
        """
        Uses the loaded SKU NN model to predict an SKU.
        Returns the predicted SKU string or None if prediction fails or model not available.
        """
        if not sku_nn_model or not sku_nn_encoder_make or not sku_nn_encoder_model or \
           not sku_nn_encoder_series or not sku_nn_tokenizer_desc or not sku_nn_encoder_referencia:
            print(
                "SKU NN model or one of its preprocessors is not loaded. Skipping NN prediction.")
            return None

        try:
            # Use our predict_sku function from sku_nn_pytorch.py
            device = 'cuda' if torch.cuda.is_available() else 'cpu'

            # Create a dictionary of encoders to pass to predict_sku
            encoders = {
                'maker': sku_nn_encoder_make,
                'model': sku_nn_encoder_model,
                'series': sku_nn_encoder_series,
                'tokenizer': sku_nn_tokenizer_desc,
                'referencia': sku_nn_encoder_referencia
            }

            # Call the predict_sku function
            predicted_sku, confidence = predict_sku(
                pytorch_model=sku_nn_model,
                encoders=encoders,
                maker=maker,
                model_year=model,
                series=series,
                descripcion=descripcion,
                device=device
            )

            if predicted_sku and predicted_sku.strip():
                print(
                    f"  SKU NN Prediction for '{descripcion}': {predicted_sku} (Confidence: {confidence:.4f})")
                return predicted_sku, confidence
            else:
                print(
                    f"  SKU NN Prediction failed for '{descripcion}' or returned empty SKU")
                return None

        except ValueError as ve:
            # This can happen if a category (maker, model, series) was not seen during training
            print(
                f"  SKU NN Prediction Error: Could not encode inputs for '{descripcion}'. Untrained category? Details: {ve}")
            return None
        except Exception as e:
            print(f"  Error during SKU NN prediction for '{descripcion}': {e}")
            return None

    def find_skus_handler(self):
        """
        Handles the 'Find SKUs' button click.
        Uses trained models to predict VIN details, processes parts, searches, and displays.
        """
        print("\n--- 'Find SKUs' button clicked ---")
        vin = self.vin_entry.get().strip().upper()
        print(f"Original VIN from entry: '{vin}'")
        # VIN correction step
        corrected_vin = self._correct_vin(vin)
        print(f"After correction: '{corrected_vin}'")
        if vin != corrected_vin:
            print(f"VIN corrected from {vin} to {corrected_vin}")
            self.vin_entry.delete(0, 'end')
            self.vin_entry.insert(0, corrected_vin)
        vin = corrected_vin

        # Clear previous results
        self._clear_results_area()

        # Clear vehicle details frame
        for widget in self.vehicle_details_frame.winfo_children():
            widget.destroy()
        ttk.Label(self.vehicle_details_frame,
                  text="Processing VIN...").pack(anchor="w", padx=5, pady=5)

        print(f"VIN Entered: {vin}")

        # Validate VIN format
        print(f"VIN validation - Length: {len(vin)}, Regex match: {bool(re.match('^[A-HJ-NPR-Z0-9]{17}$', vin))}")
        if not vin or len(vin) != 17 or not re.match("^[A-HJ-NPR-Z0-9]{17}$", vin):
            print(f"VIN validation failed for: '{vin}'")
            messagebox.showerror(
                "Invalid VIN", "VIN must be 17 alphanumeric characters (excluding I, O, Q).")
            ttk.Label(self.scrollable_frame,
                      text="Error: Invalid VIN format.").pack(anchor="nw")
            return

        # --- Predict VIN Details using Models ---
        predicted_details = self.predict_vin_details(vin)

        if not predicted_details:
            ttk.Label(self.scrollable_frame,
                      text=f"Could not predict details for VIN: {vin}.").pack(anchor="nw")
            # Optionally allow manual input here if prediction fails completely
            # self._prompt_for_manual_details(vin) # If we want fallback to manual
            return

        self.vehicle_details = predicted_details  # Store predicted details
        print(f"Predicted Vehicle Details: {self.vehicle_details}")

        # Proceed with part processing and search using predicted details
        self._process_parts_and_continue_search()

    def predict_vin_details(self, vin: str) -> dict | None:
        """Predicts maker, model, series using loaded models."""
        if not model_maker or not model or not model_series:
            print("Error: Prediction models not loaded.")
            messagebox.showerror(
                "Prediction Error", "VIN prediction models are not loaded. Cannot proceed.")
            return None

        features = extract_vin_features_production(vin)
        if not features:
            messagebox.showerror("Prediction Error",
                                 "Could not extract features from VIN.")
            return None

        details = {"maker": "N/A", "model": "N/A",
                   "series": "N/A", "Model": "N/A", "Body Class": "N/A"}

        try:
            # Predict Maker - Use DataFrame with proper column names
            import pandas as pd
            wmi_df = pd.DataFrame([[features['wmi']]], columns=['wmi'])
            wmi_encoded = encoder_x_maker.transform(wmi_df)
            # Check for unknown category before prediction
            if -1 in wmi_encoded:
                details['maker'] = "Unknown (WMI)"
            else:
                maker_pred_encoded = model_maker.predict(wmi_encoded)
                # Check for unknown category in prediction output (shouldn't happen with CategoricalNB if input known)
                if maker_pred_encoded[0] != -1:
                    make_result = encoder_y_maker.inverse_transform(
                        maker_pred_encoded.reshape(-1, 1))[0]
                    # Ensure it's a scalar value, not an array
                    if hasattr(make_result, 'item'):
                        details['maker'] = make_result.item()
                    else:
                        details['maker'] = make_result
                else:  # Should not happen if input was known, but handle defensively
                    details['maker'] = "Unknown (Prediction)"

            # Predict Year - Use DataFrame with proper column names
            year_df = pd.DataFrame([[features['year_code']]], columns=['year_code'])
            year_code_encoded = encoder_x_year.transform(year_df)
            if -1 in year_code_encoded:
                details['model'] = "Unknown (Code)"
            else:
                year_pred_encoded = model.predict(year_code_encoded)
                if year_pred_encoded[0] != -1:
                    year_result = encoder_y_year.inverse_transform(
                        year_pred_encoded.reshape(-1, 1))[0]
                    # Ensure it's a scalar value, not an array
                    if hasattr(year_result, 'item'):
                        details['model'] = year_result.item()
                    else:
                        details['model'] = year_result
                else:
                    # Fallback to direct map if model fails (unlikely for year)
                    details['model'] = str(decode_year(features['year_code'])) if decode_year(
                        features['year_code']) else "Unknown (Code)"

            # Predict Series - Use DataFrame with proper column names
            series_df = pd.DataFrame([[features['wmi'], features['vds_full']]],
                                   columns=['wmi', 'vds_full'])
            series_features_encoded = encoder_x_series.transform(series_df)
            # Check if either feature was unknown
            if -1 in series_features_encoded[0]:
                # FALLBACK STRATEGY: When VIN prediction fails, use database lookup
                print(f"    ⚠️ VIN prediction failed for WMI='{features['wmi']}', VDS='{features['vds_full']}'")
                fallback_series = self.get_most_common_series_for_wmi(features['wmi'], details['maker'])
                if fallback_series and fallback_series != "Unknown":
                    details['series'] = fallback_series
                    print(f"    🔄 Using fallback series: '{fallback_series}'")
                else:
                    details['series'] = "Unknown (VDS/WMI)"
            else:
                series_pred_encoded = model_series.predict(
                    series_features_encoded)
                if series_pred_encoded[0] != -1:
                    series_result = encoder_y_series.inverse_transform(
                        series_pred_encoded.reshape(-1, 1))[0]
                    # Ensure it's a scalar value, not an array
                    if hasattr(series_result, 'item'):
                        predicted_series = series_result.item()
                    else:
                        predicted_series = series_result

                    # Check if the prediction is meaningful or just "Unknown"
                    if predicted_series and "Unknown" not in str(predicted_series) and "N/A" not in str(predicted_series):
                        details['series'] = predicted_series
                    else:
                        # FALLBACK STRATEGY: Even when model predicts "Unknown", try database lookup
                        print(f"    ⚠️ VIN model predicted unclear series: '{predicted_series}'")
                        fallback_series = self.get_most_common_series_for_wmi(features['wmi'], details['maker'])
                        if fallback_series and fallback_series != "Unknown":
                            details['series'] = fallback_series
                            print(f"    🔄 Using fallback series: '{fallback_series}'")
                        else:
                            details['series'] = predicted_series
                else:
                    details['series'] = "Unknown (Prediction)"

            # Model and Body Class are not predicted by these models
            details['Model'] = "N/A (Not Predicted)"
            details['Body Class'] = "N/A (Not Predicted)"

            return details

        except Exception as e:
            print(f"Error during VIN prediction: {e}")
            # Handle potential errors if a feature wasn't seen during training
            messagebox.showwarning(
                "Prediction Warning", f"Could not reliably predict all details for VIN: {e}")
            # Return partially filled details if possible
            return details

    def _clear_results_area(self):
        """Clears the widgets in the scrollable results frame."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        # Removed manual input widget clearing
        self.results_placeholder_label = None
        self.save_button.config(state=tk.DISABLED)

    # Removed _prompt_for_manual_details
    # Removed _handle_manual_details_continue

    def _is_valid_sku(self, referencia: str) -> bool:
        """
        Validates if a SKU is acceptable for suggestions.
        Filters out UNKNOWN, empty, or invalid SKUs.
        """
        if not referencia or not referencia.strip():
            return False

        # Convert to uppercase for consistent checking
        sku_upper = referencia.strip().upper()

        # Filter out UNKNOWN and similar invalid values
        invalid_skus = {'UNKNOWN', 'N/A', 'NULL', 'NONE', '', 'TBD', 'PENDING', 'MANUAL'}

        if sku_upper in invalid_skus:
            print(f"    Filtered out invalid referencia: '{referencia}'")
            return False

        return True

    def _aggregate_sku_suggestions(self, suggestions: dict, new_sku: str, new_confidence: float, new_source: str) -> dict:
        """
        Aggregates SKU suggestions, handling duplicates by keeping the highest confidence.
        Also tracks all sources for transparency and applies consensus-based confidence adjustment.

        Confidence Rules:
        - Single source (Maestro only): Max 0.80-0.85 confidence (based on frequency)
        - Single source (NN only): Max 0.85 confidence
        - Single source (DB only): Max 0.80 confidence
        - Multiple sources (Maestro + NN): Can reach 1.00 confidence
        - Multiple sources (any combination): Bonus for consensus
        """
        if not self._is_valid_sku(new_sku):
            return suggestions

        if new_sku in suggestions:
            # SKU already exists - aggregate information
            existing = suggestions[new_sku]
            existing_conf = existing["confidence"]
            existing_source = existing["source"]
            existing_all_sources = existing.get("all_sources", existing_source)

            # Track all sources
            all_sources_list = existing_all_sources.split(", ") if existing_all_sources else [existing_source]
            if new_source not in all_sources_list:
                all_sources_list.append(new_source)

            combined_sources = ", ".join(all_sources_list)

            # Calculate consensus-adjusted confidence
            adjusted_confidence = self._calculate_consensus_confidence(
                max(existing_conf, new_confidence), all_sources_list
            )

            # Update with consensus-adjusted confidence
            suggestions[new_sku] = {
                "confidence": adjusted_confidence,
                "source": new_source if new_confidence > existing_conf else existing["source"],
                "all_sources": combined_sources,
                "best_confidence": max(existing_conf, new_confidence),
                "source_count": len(all_sources_list)
            }
            print(f"    🔄 Consensus update {new_sku}: {max(existing_conf, new_confidence):.3f} -> {adjusted_confidence:.3f} (Sources: {combined_sources})")
        else:
            # New SKU - add it with single-source confidence adjustment
            adjusted_confidence = self._calculate_consensus_confidence(new_confidence, [new_source])
            suggestions[new_sku] = {
                "confidence": adjusted_confidence,
                "source": new_source,
                "all_sources": new_source,
                "best_confidence": new_confidence,
                "source_count": 1
            }
            if adjusted_confidence != new_confidence:
                print(f"    📉 Single-source adjustment {new_sku}: {new_confidence:.3f} -> {adjusted_confidence:.3f} ({new_source})")

        return suggestions

    def _calculate_consensus_confidence(self, base_confidence: float, sources: list) -> float:
        """
        Calculate consensus-adjusted confidence based on prediction sources.

        Updated rules for new priority system:
        - Single source (Maestro only): Max 80-85% confidence (based on frequency)
        - Single source (NN only): Max 85% (0.85) confidence
        - Single source (DB only): Max 80% (0.80) confidence (frequency-based: 20+ = 80%)
        - NN + DB consensus: Higher value + 10% boost
        - Maestro + NN consensus: 100% (1.0) confidence
        - All three sources: 100% (1.0) confidence

        Args:
            base_confidence: Original confidence score
            sources: List of prediction sources

        Returns:
            Adjusted confidence score
        """
        if len(sources) == 1:
            # Single source - apply caps
            source = sources[0]
            if "Maestro" in source:
                return min(base_confidence, 0.85)  # 80-85% max for Maestro alone (reduced from 90%)
            elif "SKU-NN" in source or "NN" in source:
                return min(base_confidence, 0.85)  # 85% max for NN alone
            elif "DB" in source:
                return min(base_confidence, 0.80)  # 80% max for DB alone (increased from 70%)
            else:
                return min(base_confidence, 0.80)  # Default single source cap

        else:
            # Multiple sources - consensus bonus
            has_maestro = any("Maestro" in source for source in sources)
            has_nn = any("SKU-NN" in source or "NN" in source for source in sources)
            has_db = any("DB" in source for source in sources)

            # All three sources = 100% confidence
            if has_maestro and has_nn and has_db:
                return 1.00

            # Maestro + NN consensus = 100% confidence
            elif has_maestro and has_nn:
                return 1.00

            # NN + DB consensus: Higher value + 10% boost
            elif has_nn and has_db:
                return min(base_confidence + 0.10, 0.95)

            # Other multi-source combinations get smaller bonus
            elif len(sources) >= 2:
                return min(base_confidence + 0.05, 0.90)

            return base_confidence

    def _process_parts_and_continue_search(self):
        """Processes part descriptions and triggers the search and display."""
        # (Content remains largely the same, uses self.vehicle_details which is now predicted)
        part_descriptions_raw = self.parts_text.get("1.0", tk.END).strip()
        self.processed_parts = []
        if part_descriptions_raw:
            original_descripcions = [
                line.strip() for line in part_descriptions_raw.splitlines() if line.strip()]
            print(f"Original Descriptions List: {original_descripcions}")
            for original_desc in original_descripcions:
                print(f"  Processing: '{original_desc}'")

                # STEP 1: Apply user corrections FIRST (highest priority)
                corrected_desc = self.apply_user_corrections(original_desc)
                if corrected_desc != original_desc:
                    print(f"  ✅ User correction applied: '{original_desc}' → '{corrected_desc}'")

                # STEP 2: Normalize the corrected description (without synonym expansion)
                normalized_original = self.enhanced_normalize_text(corrected_desc)
                print(f"  Normalized original: '{normalized_original}'")

                # STEP 3: Apply synonym expansion for fallback searches (use corrected description)
                expanded_desc = self.expand_synonyms(corrected_desc)
                print(f"  After synonym expansion: '{expanded_desc}'")
                normalized_expanded = self.enhanced_normalize_text(expanded_desc)
                print(f"  Normalized expanded: '{normalized_expanded}'")

                # STEP 4: Create abbreviated version to match database format
                abbreviated_desc = self.create_abbreviated_version(normalized_original)
                print(f"  Abbreviated version: '{abbreviated_desc}'")

                # STEP 5: Look up equivalencia ID using the expanded form (CASE-INSENSITIVE)
                equivalencia_id = equivalencias_map_global.get(normalized_expanded.lower())

                # STEP 4: If no direct match, try fuzzy matching as fallback
                if equivalencia_id is None:
                    fuzzy_normalized_desc = self.enhanced_normalize_text(expanded_desc, use_fuzzy=True)
                    equivalencia_id = equivalencias_map_global.get(fuzzy_normalized_desc.lower())

                    if equivalencia_id is not None:
                        normalized_expanded = fuzzy_normalized_desc
                        print(f"  Found via fuzzy normalization: EqID {equivalencia_id}")

                    # Fuzzy equivalencias matching removed - only exact matches
                    if equivalencia_id is None:
                        print(f"  No exact equivalencia match found for: '{normalized_expanded}'")

                self.processed_parts.append({
                    "original": original_desc,
                    "normalized_original": normalized_original,  # Store original normalized form
                    "expanded": expanded_desc,  # Store the synonym-expanded form
                    "normalized_expanded": normalized_expanded,  # Store expanded normalized form
                    "abbreviated": abbreviated_desc,  # Store abbreviated form for database matching
                    "equivalencia_id": equivalencia_id
                })
                print(f"  Final result: '{original_desc}' -> Original normalized: '{normalized_original}' -> Abbreviated: '{abbreviated_desc}' -> Expanded: '{expanded_desc}' -> Expanded normalized: '{normalized_expanded}', EqID: {equivalencia_id}")
        else:
            print("No part descriptions entered.")
            self.processed_parts = []

        # --- Phase 4: Search Logic ---
        self.current_suggestions = {}
        self.selection_vars = {}

        db_conn = None
        try:
            print(f"Connecting to database: {DEFAULT_DB_PATH}")
            if not os.path.exists(DEFAULT_DB_PATH):
                messagebox.showerror(
                    "Database Error", f"Database file not found at {DEFAULT_DB_PATH}. Please run the offline processor first.")
                ttk.Label(self.scrollable_frame, text=f"Error: Database not found at {DEFAULT_DB_PATH}").pack(
                    anchor="nw")
                return

            db_conn = sqlite3.connect(DEFAULT_DB_PATH)
            cursor = db_conn.cursor()

            # Apply database optimizations for better performance
            cursor.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrent access
            cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
            cursor.execute("PRAGMA temp_store=memory")  # Use memory for temp tables
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory map

            print("Database connection successful with optimized settings.")

            for part_info in self.processed_parts:
                original_desc = part_info["original"]
                normalized_original = part_info["normalized_original"]
                expanded_desc = part_info["expanded"]
                normalized_expanded = part_info["normalized_expanded"]
                abbreviated_desc = part_info["abbreviated"]
                eq_id = part_info["equivalencia_id"]
                print(
                    f"\nSearching for: '{original_desc}' (Original normalized: '{normalized_original}', Abbreviated: '{abbreviated_desc}', Expanded: '{expanded_desc}', Expanded normalized: '{normalized_expanded}', EqID: {eq_id})")

                suggestions = {}

                # Use self.vehicle_details which is now PREDICTED
                predicted_make_val = self.vehicle_details.get('maker', 'N/A')

                # Cache disabled - proceed with fresh predictions
                if isinstance(predicted_make_val, np.ndarray):
                    maker_raw = str(predicted_make_val.item()) if predicted_make_val.size > 0 else 'N/A'
                else:
                    maker_raw = str(predicted_make_val) if pd.notna(predicted_make_val) else 'N/A'

                # Fix make case - database AND Maestro use proper case, not uppercase
                # Based on database analysis: 'Renault', 'Chevrolet', 'Ford', 'Mazda', etc.
                make_case_map = {
                    'RENAULT': 'Renault',
                    'CHEVROLET': 'Chevrolet',
                    'MAZDA': 'Mazda',
                    'FORD': 'Ford',
                    'HYUNDAI': 'Hyundai',
                    'TOYOTA': 'Toyota',
                    'NISSAN': 'Nissan',
                    'KIA': 'Kia',
                    'VOLKSWAGEN': 'Volkswagen'
                }
                maker = make_case_map.get(maker_raw.upper(), maker_raw)
                print(f"  🔧 Make case correction: '{maker_raw}' -> '{maker}'")
                print(f"  Make case correction: '{maker_raw}' -> '{maker}'")

                # Model is likely N/A from predictor
                vin_model = self.vehicle_details.get('Model', 'N/A')
                model_str = self.vehicle_details.get('model', 'N/A')
                model = None  # Initialize
                # Check if it's still an array element
                if isinstance(model_str, np.ndarray):
                    model_str_scalar = model_str.item()  # Extract scalar value
                else:
                    model_str_scalar = model_str  # Use as is if already scalar/string

                if model_str_scalar and model_str_scalar != 'N/A':
                    try:
                        model = int(model_str_scalar)
                    except (ValueError, TypeError):
                        print(
                            f"Warning: Could not convert predicted year '{model_str_scalar}' to integer.")
                        model = None  # Ensure it's None if conversion fails

                # Enhanced Maestro Search with 3-parameter exact + fuzzy description matching
                print(f"  Searching Maestro data ({len(maestro_data_global)} entries)...")

                # Get predicted series for matching
                predicted_series_val = self.vehicle_details.get('series', 'N/A')
                if isinstance(predicted_series_val, np.ndarray):
                    series = str(predicted_series_val.item()) if predicted_series_val.size > 0 else 'N/A'
                else:
                    series = str(predicted_series_val) if pd.notna(predicted_series_val) else 'N/A'

                # Apply runtime series normalization (hybrid approach - Phase 2)
                original_series = series
                if series and series != 'N/A':
                    normalized_series = self.normalize_series(maker, series)
                    if normalized_series != series:
                        print(f"    🔄 Series normalized at runtime: {maker}/{series} → {normalized_series}")
                        series = normalized_series

                # Debug: Show what we're searching for
                print(f"    🔍 Searching for: maker='{maker}', model='{model_str_scalar}', series='{series}'" +
                      (f" (normalized from '{original_series}')" if series != original_series else ""))
                print(f"    🔍 Description (original): '{normalized_original}'")
                print(f"    🔍 Description (expanded): '{normalized_expanded}'")

                # First pass: Exact matches on maker, model, series + exact description
                # COLLECT ALL MATCHING SKUs (not just first one)
                maestro_exact_matches = []
                maestro_matches_found = 0

                for maestro_entry in maestro_data_global:
                    maestro_make = str(maestro_entry.get('maker', ''))
                    maestro_year = str(maestro_entry.get('model', ''))
                    maestro_series = str(maestro_entry.get('series', ''))
                    maestro_desc = str(maestro_entry.get('descripcion', '')).lower()

                    # Check 3-parameter exact match (maker, model, series) - CASE INSENSITIVE
                    make_match = maestro_make.upper() == maker.upper()
                    # Normalize year comparison - handle both float and string formats
                    maestro_year_normalized = str(int(float(maestro_year))) if maestro_year and str(maestro_year).replace('.', '').isdigit() else str(maestro_year)
                    year_match = maestro_year_normalized == model_str_scalar
                    series_match = maestro_series.upper() == series.upper()

                    # Debug: Show first few comparisons
                    if maestro_matches_found < 5:
                        print(f"    📋 Entry {maestro_matches_found}: maker='{maestro_make.upper()}' vs '{maker.upper()}' ({make_match})")
                        print(f"    📋 Entry {maestro_matches_found}: model='{maestro_year}' vs '{model_str_scalar}' ({year_match})")
                        print(f"    📋 Entry {maestro_matches_found}: series='{maestro_series.upper()}' vs '{series.upper()}' ({series_match})")
                        print(f"    📋 Entry {maestro_matches_found}: Desc='{maestro_desc}' vs '{normalized_original}' / '{normalized_expanded}'")
                        maestro_matches_found += 1

                    if make_match and year_match and series_match:
                        # Apply unified preprocessing for exact description matching
                        preprocessed_maestro_desc = self.unified_text_preprocessing(maestro_desc)
                        preprocessed_original = self.unified_text_preprocessing(original_desc)
                        preprocessed_expanded = self.unified_text_preprocessing(expanded_desc)

                        # Check for exact description match after unified preprocessing
                        desc_match_orig = preprocessed_maestro_desc == preprocessed_original
                        desc_match_exp = preprocessed_maestro_desc == preprocessed_expanded
                        desc_match = desc_match_orig or desc_match_exp

                        if desc_match:
                            referencia = maestro_entry.get('referencia')
                            if referencia and referencia.strip():
                                # Store match for frequency analysis
                                maestro_exact_matches.append({
                                    'referencia': referencia,
                                    'match_type': "original" if desc_match_orig else "expanded",
                                    'preprocessed_desc': preprocessed_maestro_desc
                                })

                # Process ALL Maestro exact matches with frequency-based ordering
                if maestro_exact_matches:
                    # Count frequency of each SKU
                    sku_frequency = {}
                    for match in maestro_exact_matches:
                        referencia = match['referencia']
                        sku_frequency[referencia] = sku_frequency.get(referencia, 0) + 1

                    # Sort SKUs by frequency (most repeated first)
                    sorted_skus = sorted(sku_frequency.items(), key=lambda x: x[1], reverse=True)

                    print(f"    ✅ Found {len(maestro_exact_matches)} Maestro exact matches for {len(sorted_skus)} unique SKUs")

                    # Add ALL unique SKUs to suggestions (ordered by frequency)
                    for referencia, frequency in sorted_skus:
                        # Maestro base confidence: 80-85% (adjusted from 90%)
                        maestro_confidence = 0.85 if frequency >= 3 else 0.80  # Higher confidence for repeated entries
                        suggestions = self._aggregate_sku_suggestions(
                            suggestions, referencia, maestro_confidence, "Maestro")
                        print(f"    ✅ Maestro referencia: {referencia} (Frequency: {frequency}, Conf: {maestro_confidence})")

                        # Show match details for first occurrence
                        first_match = next(m for m in maestro_exact_matches if m['referencia'] == referencia)
                        print(f"      Matched via {first_match['match_type']}: '{first_match['preprocessed_desc']}'")

                # Fuzzy description matching removed - only exact matches for Maestro
                if not suggestions:
                    print("    No exact matches found in Maestro. Fuzzy description matching disabled for accuracy.")

                # --- Maestro Fallback: Make + Year Only (when Series prediction fails) ---
                if not suggestions and (series == 'Unknown (VDS/WMI)' or series == 'N/A'):
                    print(f"  🔄 Maestro Fallback: Series prediction failed ('{series}'), trying Make + Year + Description matching...")

                    fallback_matches = []
                    for maestro_entry in maestro_data_global:
                        maestro_make = str(maestro_entry.get('maker', ''))
                        maestro_year = str(maestro_entry.get('model', ''))
                        maestro_desc = str(maestro_entry.get('normalized_descripcion', '')).lower()

                        # Normalize year comparison
                        maestro_year_normalized = str(int(float(maestro_year))) if maestro_year and str(maestro_year).replace('.', '').isdigit() else str(maestro_year)

                        # Check Make + Year match only
                        make_match = maestro_make.upper() == maker.upper()
                        year_match = maestro_year_normalized == model_str_scalar

                        if make_match and year_match:
                            # Apply unified preprocessing for description matching
                            preprocessed_maestro_desc = self.unified_text_preprocessing(maestro_desc)
                            preprocessed_original = self.unified_text_preprocessing(original_desc)
                            preprocessed_expanded = self.unified_text_preprocessing(expanded_desc)

                            # Check for exact description match after unified preprocessing
                            desc_match_orig = preprocessed_maestro_desc == preprocessed_original
                            desc_match_exp = preprocessed_maestro_desc == preprocessed_expanded

                            if desc_match_orig or desc_match_exp:
                                referencia = maestro_entry.get('referencia')
                                if referencia and referencia.strip() and referencia.strip().upper() != 'UNKNOWN':
                                    match_type = "Original" if desc_match_orig else "Expanded"
                                    fallback_matches.append({
                                        'referencia': referencia.strip(),
                                        'entry': maestro_entry,
                                        'match_type': f"Fallback-{match_type}",
                                        'series': maestro_entry.get('series', 'N/A')
                                    })
                                    print(f"    ✅ Fallback match: {referencia} (series: {maestro_entry.get('series', 'N/A')})")

                    # Process fallback matches with lower confidence (since series wasn't matched)
                    if fallback_matches:
                        print(f"  ✅ Found {len(fallback_matches)} Maestro fallback matches (Make + Year + Description)")

                        # Count frequency of each SKU
                        sku_frequency = {}
                        for match in fallback_matches:
                            referencia = match['referencia']
                            sku_frequency[referencia] = sku_frequency.get(referencia, 0) + 1

                        # Sort by frequency (most repeated first)
                        sorted_skus = sorted(sku_frequency.items(), key=lambda x: x[1], reverse=True)

                        # Add SKUs with reduced confidence (0.75 instead of 0.90)
                        for referencia, frequency in sorted_skus:
                            print(f"     📋 Maestro Fallback referencia: {referencia} (frequency: {frequency})")
                            suggestions = self._aggregate_sku_suggestions(suggestions, referencia, 0.75, "Maestro-Fallback")
                    else:
                        print(f"  ❌ No Maestro fallback matches found")



                # --- Neural Network Prediction (Priority 2) ---
                # Use the already normalized series from above (consistent across all prediction sources)
                series_str_for_nn = series  # This is already normalized

                if maker != 'N/A' and model_str_scalar != 'N/A' and series_str_for_nn != 'N/A':
                    print(f"  🔄 Applying unified preprocessing for Neural Network input...")

                    # Apply unified preprocessing to input descriptions for Neural Network
                    preprocessed_original = self.unified_text_preprocessing(original_desc)
                    preprocessed_expanded = self.unified_text_preprocessing(expanded_desc)

                    print(f"  Attempting SKU NN prediction for: maker='{maker}', model='{model_str_scalar}', series='{series_str_for_nn}'")
                    print(f"  NN Input (preprocessed original): '{preprocessed_original}'")
                    print(f"  NN Input (preprocessed expanded): '{preprocessed_expanded}'")

                    # Try preprocessed original description first
                    sku_nn_output = self._get_sku_nn_prediction(
                        maker=maker,
                        model=model_str_scalar,
                        series=series_str_for_nn,
                        descripcion=preprocessed_original
                    )

                    # If no good result, try preprocessed expanded description
                    if not sku_nn_output or (sku_nn_output and sku_nn_output[1] < 0.7):
                        print(f"  Trying NN prediction with preprocessed expanded description...")
                        sku_nn_output_expanded = self._get_sku_nn_prediction(
                            maker=maker,
                            model=model_str_scalar,
                            series=series_str_for_nn,
                            descripcion=preprocessed_expanded
                        )
                        # Use expanded result if it's better
                        if sku_nn_output_expanded and (not sku_nn_output or sku_nn_output_expanded[1] > sku_nn_output[1]):
                            sku_nn_output = sku_nn_output_expanded

                    if sku_nn_output:
                        nn_sku, nn_confidence = sku_nn_output
                        if nn_sku and nn_sku.strip():  # Add if not empty
                            suggestions = self._aggregate_sku_suggestions(
                                suggestions, nn_sku, float(nn_confidence), "SKU-NN")
                            print(f"    Found via SKU-NN: {nn_sku} (Conf: {nn_confidence:.4f})")
                else:
                    print("  Skipping SKU NN prediction due to missing Make, Year, or Series from VIN prediction.")
                # --- End Neural Network Prediction ---

                # --- Year Range Database Optimization (Priority 3) ---
                if self.year_range_optimizer and model is not None and series.upper() != 'N/A':
                    print(f"  🚀 Searching Year Range Database (maker: {maker}, model: {model}, series: {series})...")
                    try:
                        # Try with original description first
                        year_range_predictions = self.year_range_optimizer.get_sku_predictions_year_range(
                            maker=maker,
                            model=model,
                            series=series,
                            description=original_desc,
                            limit=10
                        )

                        if year_range_predictions:
                            print(f"    ✅ Found {len(year_range_predictions)} year range predictions (original desc)")
                            for pred in year_range_predictions:
                                suggestions = self._aggregate_sku_suggestions(
                                    suggestions, pred['sku'], pred['confidence'], f"Year-Range ({pred['year_range']})")
                                print(f"    📅 Year Range: {pred['sku']} (Freq: {pred['frequency']}, Range: {pred['year_range']}, Conf: {pred['confidence']:.3f})")

                        # If no results with original, try with normalized description
                        if not year_range_predictions:
                            year_range_predictions = self.year_range_optimizer.get_sku_predictions_year_range(
                                maker=maker,
                                model=model,
                                series=series,
                                description=normalized_original,
                                limit=10
                            )

                            if year_range_predictions:
                                print(f"    ✅ Found {len(year_range_predictions)} year range predictions (normalized desc)")
                                for pred in year_range_predictions:
                                    suggestions = self._aggregate_sku_suggestions(
                                        suggestions, pred['sku'], pred['confidence'], f"Year-Range ({pred['year_range']})")
                                    print(f"    📅 Year Range: {pred['sku']} (Freq: {pred['frequency']}, Range: {pred['year_range']}, Conf: {pred['confidence']:.3f})")

                        if not year_range_predictions:
                            print(f"    ❌ No year range matches found")

                    except Exception as e:
                        print(f"    ⚠️ Year range optimization error: {e}")
                # --- End Year Range Database Optimization ---











                sorted_suggestions = sorted(
                    suggestions.items(), key=lambda item: item[1]['confidence'], reverse=True)
                self.current_suggestions[original_desc] = sorted_suggestions
                print(
                    f"  Suggestions for '{original_desc}': {sorted_suggestions}")

                # Cache disabled - no caching of results

        except Exception as e:
            messagebox.showerror(
                "Search Error", f"An error occurred during search: {e}")
            print(f"Error during search phase: {e}")
            ttk.Label(self.scrollable_frame,
                      text=f"Error during search: {e}").pack(anchor="nw")
        finally:
            if db_conn:
                db_conn.close()
                print("Database connection closed.")

        # --- Update Results Display ---
        self.display_results()  # Call method to update GUI

    def display_results(self):
        """Updates the vehicle details frame and scrollable results frame with SKU suggestions."""
        # Clear previous results
        self._clear_results_area()

        # Update Vehicle Details in the right column frame
        # First, clear any existing content in the vehicle details frame
        for widget in self.vehicle_details_frame.winfo_children():
            widget.destroy()

        # Display Vehicle Details in the right column frame
        if self.vehicle_details:
            vin = self.vin_entry.get().strip().upper()
            ttk.Label(self.vehicle_details_frame, text=f"VIN: {vin}").pack(
                anchor="w", padx=5, pady=2)
            ttk.Label(
                self.vehicle_details_frame, text=f"Predicted maker: {self.vehicle_details.get('maker', 'N/A')}").pack(anchor="w", padx=5, pady=2)
            ttk.Label(
                self.vehicle_details_frame, text=f"Predicted model: {self.vehicle_details.get('model', 'N/A')}").pack(anchor="w", padx=5, pady=2)
            ttk.Label(
                self.vehicle_details_frame, text=f"Predicted series: {self.vehicle_details.get('series', 'N/A')}").pack(anchor="w", padx=5, pady=2)
        else:
            ttk.Label(self.vehicle_details_frame,
                      text="Vehicle details could not be predicted.").pack(anchor="w", padx=5, pady=5)

        # Display SKU Suggestions (Tasks 5.2, 5.3, 5.4) - Remains the same logic
        if not self.processed_parts:
            ttk.Label(self.scrollable_frame,
                      text="\nNo part descriptions were entered.").pack(anchor="nw")
        elif not self.current_suggestions and self.processed_parts:
            ttk.Label(self.scrollable_frame,
                      text="\nNo suggestions found for the entered descriptions.").pack(anchor="nw")
        elif self.current_suggestions:
            # Add a small separator but no redundant header
            ttk.Separator(self.scrollable_frame, orient='horizontal').pack(
                fill='x', pady=5)

            # Create a container frame for the responsive grid
            self.results_grid_container = ttk.Frame(self.scrollable_frame)
            self.results_grid_container.pack(
                fill="both", expand=True, padx=5, pady=5)  # Fill both to get width

            # Set a minimum width to ensure proper layout calculation
            self.results_grid_container.config(
                width=self.root.winfo_width() - 50)

            # Clear previous part frames widgets list
            self.part_frames_widgets = []

            # Reset the current number of columns to force recalculation
            self.current_num_columns = 0

            # Create frames for each part description
            for part_info in self.processed_parts:
                original_desc = part_info["original"]
                normalized_original = part_info["normalized_original"]

                # Apply user corrections first (highest priority), then use normalized version
                corrected_desc = self.apply_user_corrections(original_desc)
                if corrected_desc != original_desc:
                    # User correction exists - use it for display
                    display_desc = corrected_desc.upper()
                    print(f"🎯 Display using phrase correction: '{original_desc}' → '{display_desc}'")
                else:
                    # No user correction - apply the same processing as during search
                    # This ensures display matches the processed version used for search
                    processed_desc = self.enhanced_normalize_text(original_desc)
                    display_desc = processed_desc.upper() if processed_desc else original_desc.upper()
                    print(f"🎯 Display using enhanced processing: '{original_desc}' → '{processed_desc}' → '{display_desc}'")

                # Get suggestions and apply source-specific limits
                all_suggestions = [(referencia, info) for referencia, info in self.current_suggestions.get(original_desc, [])
                                   if referencia and referencia.strip()]

                # Apply source-specific limits: Maestro=unlimited, NN=2, DB=2
                maestro_suggestions = []
                nn_suggestions = []
                db_suggestions = []

                for referencia, info in all_suggestions:
                    source = info.get('source', '')
                    if 'Maestro' in source:
                        maestro_suggestions.append((referencia, info))
                    elif 'NN' in source or 'Neural' in source:
                        if len(nn_suggestions) < 2:  # Limit NN to 2 results
                            nn_suggestions.append((referencia, info))
                    elif 'DB' in source or 'Database' in source:
                        if len(db_suggestions) < 2:  # Limit DB to 2 results
                            db_suggestions.append((referencia, info))
                    else:
                        # Handle other sources (fuzzy, etc.) - treat as DB for now
                        if len(db_suggestions) < 2:
                            db_suggestions.append((referencia, info))

                # Combine all limited suggestions and sort by confidence
                suggestions_list = maestro_suggestions + nn_suggestions + db_suggestions
                suggestions_list.sort(key=lambda x: x[1].get('confidence', 0), reverse=True)

                print(f"    📊 Results for '{original_desc}': Maestro={len(maestro_suggestions)}, NN={len(nn_suggestions)}, DB={len(db_suggestions)}, Total={len(suggestions_list)}")

                # Create part frame with header that includes correction button
                part_frame = ttk.LabelFrame(
                    self.results_grid_container, text="", padding=5)
                self.part_frames_widgets.append(part_frame)
                part_frame.columnconfigure(0, weight=1)

                # Set consistent card width based on content
                # Wider cards for better text display but still responsive
                card_width = 280  # Increased from 200 to accommodate 2-line descriptions
                part_frame.config(width=card_width, height=150)  # Set minimum height too

                # Create header frame with description and pencil icon
                header_frame = ttk.Frame(part_frame)
                header_frame.pack(fill="x", padx=5, pady=(0, 5))
                header_frame.columnconfigure(0, weight=1)

                # Description label with text wrapping
                # Calculate max width based on average character width
                max_chars_per_line = 25  # Adjust based on desired card width

                # Wrap text if it's too long
                if len(display_desc) > max_chars_per_line:
                    # Simple word wrapping - split at spaces when possible
                    words = display_desc.split()
                    lines = []
                    current_line = ""

                    for word in words:
                        if len(current_line + " " + word) <= max_chars_per_line:
                            current_line = current_line + " " + word if current_line else word
                        else:
                            if current_line:
                                lines.append(current_line)
                                current_line = word
                            else:
                                # Word is longer than max_chars_per_line, truncate it
                                lines.append(word[:max_chars_per_line-3] + "...")
                                current_line = ""

                    if current_line:
                        lines.append(current_line)

                    # Limit to 2 lines maximum
                    if len(lines) > 2:
                        lines = lines[:2]
                        lines[1] = lines[1][:max_chars_per_line-3] + "..."

                    wrapped_text = "\n".join(lines)
                else:
                    wrapped_text = display_desc

                desc_label = ttk.Label(
                    header_frame,
                    text=wrapped_text,
                    font=("", 10, "bold"),
                    justify="left",
                    wraplength=0  # Disable automatic wrapping since we handle it manually
                )
                desc_label.grid(row=0, column=0, sticky="w")

                # Pencil icon button for corrections
                pencil_button = ttk.Button(
                    header_frame,
                    text="✏️",
                    width=3,
                    command=lambda desc=original_desc, display=display_desc: self.open_correction_dialog(desc, display)
                )
                pencil_button.grid(row=0, column=1, sticky="e", padx=(5, 0))

                # Add separator
                ttk.Separator(part_frame, orient='horizontal').pack(fill='x', pady=5)

                if suggestions_list:
                    # Check for auto-preselection (1.00 confidence)
                    auto_preselect_sku = None
                    top_suggestion = suggestions_list[0] if suggestions_list else None
                    if top_suggestion:
                        top_sku, top_info = top_suggestion
                        top_confidence = top_info.get('confidence', 0)
                        if top_confidence >= 1.00:
                            auto_preselect_sku = top_sku
                            print(f"🎯 Auto-preselecting {top_sku} for '{original_desc}' (Confidence: {top_confidence:.2f})")

                    self.selection_vars[original_desc] = tk.StringVar(
                        value=auto_preselect_sku)  # Auto-preselect if 1.00 confidence
                    self.manual_sku_vars = getattr(self, 'manual_sku_vars', {})
                    self.manual_sku_vars[original_desc] = tk.StringVar()

                    # Add preselection indicator if auto-preselected
                    if auto_preselect_sku:
                        preselect_label = ttk.Label(
                            part_frame,
                            text="🎯 Auto-selected (1.00 confidence) - You can change this selection:",
                            foreground="green",
                            font=("", 9, "italic")
                        )
                        preselect_label.pack(anchor="w", padx=5, pady=2)

                    ttk.Separator(part_frame, orient='horizontal').pack(
                        fill='x', pady=5)

                    # Add radio buttons for each suggestion
                    for referencia, info in suggestions_list:
                        conf = info.get('confidence', 0)
                        source = info.get('source', '')
                        all_sources = info.get('all_sources', source)

                        # Show all sources if multiple, otherwise just the main source
                        display_source = all_sources if all_sources != source else source

                        # Shorten source names for better UI display
                        short_source = self._shorten_source_name(display_source)

                        rb = ttk.Radiobutton(
                            part_frame,
                            text=f"{referencia} ({self._format_confidence_percentage(conf)}, {short_source})",
                            variable=self.selection_vars[original_desc],
                            value=referencia
                        )
                        rb.pack(anchor="w", padx=5, pady=2)

                    # Manual entry option
                    rb_none_frame = ttk.Frame(part_frame)
                    rb_none_frame.pack(anchor="w", padx=5, pady=2, fill="x")
                    rb_none = ttk.Radiobutton(
                        rb_none_frame,
                        text="Manual Entry:",
                        variable=self.selection_vars[original_desc],
                        value="MANUAL"
                    )
                    rb_none.pack(side=tk.LEFT, padx=(0, 5))
                    manual_entry = ttk.Entry(
                        rb_none_frame,
                        textvariable=self.manual_sku_vars[original_desc],
                        width=15
                    )
                    manual_entry.pack(side=tk.LEFT, padx=5)

                    def _on_manual_entry_change(*_, desc=original_desc):
                        if self.manual_sku_vars[desc].get().strip():
                            self.selection_vars[desc].set("MANUAL")
                    self.manual_sku_vars[original_desc].trace_add(
                        "write", _on_manual_entry_change)

                    # 'I don't know' option
                    rb_unknown_frame = ttk.Frame(part_frame)
                    rb_unknown_frame.pack(anchor="w", padx=5, pady=2, fill="x")
                    rb_unknown = ttk.Radiobutton(
                        rb_unknown_frame,
                        text="I don't know the SKU",
                        variable=self.selection_vars[original_desc],
                        value="UNKNOWN"
                    )
                    rb_unknown.pack(side=tk.LEFT, fill="x", expand=True)
                else:
                    # No suggestions, only manual and unknown options
                    self.selection_vars[original_desc] = tk.StringVar(
                        value=None)
                    self.manual_sku_vars = getattr(self, 'manual_sku_vars', {})
                    self.manual_sku_vars[original_desc] = tk.StringVar()
                    rb_none_frame = ttk.Frame(part_frame)
                    rb_none_frame.pack(anchor="w", padx=5, pady=2, fill="x")
                    rb_none = ttk.Radiobutton(
                        rb_none_frame,
                        text="Manual Entry:",
                        variable=self.selection_vars[original_desc],
                        value="MANUAL"
                    )
                    rb_none.pack(side=tk.LEFT, padx=(0, 5))
                    manual_entry = ttk.Entry(
                        rb_none_frame,
                        textvariable=self.manual_sku_vars[original_desc],
                        width=15
                    )
                    manual_entry.pack(side=tk.LEFT, padx=5)

                    def _on_manual_entry_change(*_, desc=original_desc):
                        if self.manual_sku_vars[desc].get().strip():
                            self.selection_vars[desc].set("MANUAL")
                    self.manual_sku_vars[original_desc].trace_add(
                        "write", _on_manual_entry_change)
                    rb_unknown_frame = ttk.Frame(part_frame)
                    rb_unknown_frame.pack(anchor="w", padx=5, pady=2, fill="x")
                    rb_unknown = ttk.Radiobutton(
                        rb_unknown_frame,
                        text="I don't know the SKU",
                        variable=self.selection_vars[original_desc],
                        value="UNKNOWN"
                    )
                    rb_unknown.pack(side=tk.LEFT, fill="x", expand=True)

            # Initial layout + bind configure event for responsiveness
            print("Initializing responsive layout...")
            self.root.update_idletasks()  # Force geometry update before calculating layout
            self._resize_results_columns()  # Perform initial layout
            self.results_grid_container.bind(
                "<Configure>", self._on_results_configure)
            self.root.bind("<Configure>", self._on_results_configure)
            if self.processed_parts:
                self.save_button.config(state=tk.NORMAL)
            else:
                self.save_button.config(state=tk.DISABLED)

    def _on_results_configure(self, _=None):
        # This method is called when the results_grid_container is resized
        # We add a small delay (debounce) to avoid excessive re-layouts during rapid resizing
        # The event parameter is unused but required by the bind method
        if hasattr(self, '_after_id_resize'):
            self.root.after_cancel(self._after_id_resize)
        self._after_id_resize = self.root.after(
            100, self._resize_results_columns)

    def _resize_results_columns(self):
        """Recalculates and applies the grid layout for part_frames to create a responsive layout."""
        if not hasattr(self, 'results_grid_container') or not self.results_grid_container.winfo_exists():
            return
        if not self.part_frames_widgets:  # No items to grid
            return

        # Get the current width of the container
        container_width = self.results_grid_container.winfo_width()

        # If the container width is not yet initialized, use the root window width as a fallback
        if container_width <= 1:
            container_width = self.root.winfo_width() - 40  # Subtract some padding

        # Get the actual width of a part frame by measuring the first one
        # This ensures we use the real width rather than an estimate
        if self.part_frames_widgets:
            # Update the first widget to ensure its size is calculated
            self.part_frames_widgets[0].update_idletasks()
            # Add padding (increased for new wider cards)
            actual_item_width = self.part_frames_widgets[0].winfo_reqwidth() + 15
        else:
            actual_item_width = 295  # Updated fallback for new card width (280 + 15 padding)

        # Calculate the number of columns that can fit completely
        # We only want to show complete columns (no partial columns)
        if container_width <= actual_item_width:
            num_columns = 1
        else:
            # Calculate how many complete columns can fit
            num_columns = max(1, int(container_width / actual_item_width))

            # Ensure we don't create more columns than we have items
            num_columns = min(num_columns, len(self.part_frames_widgets))

            # Apply intelligent column reduction based on content complexity
            # If we have many long descriptions, reduce columns for better readability
            if hasattr(self, 'processed_parts') and self.processed_parts:
                avg_desc_length = sum(len(part["original"]) for part in self.processed_parts) / len(self.processed_parts)

                # If average description length is long, reduce columns
                if avg_desc_length > 40 and num_columns > 3:
                    num_columns = 3  # Max 3 columns for long descriptions
                elif avg_desc_length > 60 and num_columns > 2:
                    num_columns = 2  # Max 2 columns for very long descriptions

        print(
            f"Container width: {container_width}, Item width: {actual_item_width}, Complete columns: {num_columns}")

        # Check if we need to update the layout
        layout_needs_update = (
            num_columns != self.current_num_columns or
            self.current_num_columns == 0 or
            len(self.results_grid_container.grid_slaves()) != len(
                self.part_frames_widgets)
        )

        if not layout_needs_update:
            # Further check if all columns have the correct weight
            all_weights_correct = True
            for i in range(num_columns):
                if self.results_grid_container.grid_columnconfigure(i).get('weight', '0') != '1':
                    all_weights_correct = False
                    break

            if all_weights_correct:
                return  # No layout change needed

        # Update the layout

        # 1. Clear all existing column configurations
        current_configured_cols = max(self.current_num_columns,
                                      self.results_grid_container.grid_size()[0])
        for i in range(current_configured_cols):
            self.results_grid_container.columnconfigure(i, weight=0)

        # 2. Remove all widgets from the grid
        for widget in self.results_grid_container.grid_slaves():
            widget.grid_forget()

        # 3. Configure the new columns with equal weight
        for i in range(num_columns):
            self.results_grid_container.columnconfigure(i, weight=1)

        # 4. Update the current number of columns
        self.current_num_columns = num_columns

        # 5. Re-grid all the part frames in the new layout
        for idx, frame_widget in enumerate(self.part_frames_widgets):
            row = idx // num_columns
            col = idx % num_columns
            frame_widget.grid(row=row, column=col, padx=5,
                              pady=5, sticky="nsew")

        print(
            f"Updated layout to {num_columns} complete columns with {len(self.part_frames_widgets)} items")

    # The _toggle_manual_entry method is no longer needed as manual entry is always visible

    # The _confirm_manual_sku method is no longer needed as the manual entry
    # automatically selects the radio button and will be saved with the "Save Confirmed Selections" button

    def save_selections_handler(self):
        """
        Handles the 'Save Confirmed Selections' button click.
        Gathers selected SKUs, adds them to the in-memory Maestro data,
        and writes the updated data back to Maestro.xlsx.
        (Corresponds to Tasks 5.6, 5.7, 5.8)
        """
        global maestro_data_global
        print("\n--- 'Save Confirmed Selections' clicked ---")
        if not self.vehicle_details or not self.processed_parts:
            messagebox.showwarning(
                "Cannot Save", "No valid search results available to save.")
            return

        selections_to_save = []
        for part_info in self.processed_parts:
            original_desc = part_info["original"]
            selected_sku_var = self.selection_vars.get(original_desc)
            if selected_sku_var:
                selected_sku = selected_sku_var.get()
                if selected_sku:
                    # Check if this is a manually entered SKU or unknown
                    if selected_sku == "UNKNOWN":
                        print(f"Skipping UNKNOWN SKU for '{original_desc}' - not saving to Maestro")
                        continue  # Skip UNKNOWN entries - don't save them to Maestro
                    elif selected_sku == "MANUAL":
                        # Get the actual SKU from the manual entry field
                        manual_sku_var = self.manual_sku_vars.get(original_desc)
                        if manual_sku_var:
                            actual_manual_sku = manual_sku_var.get().strip()
                            if actual_manual_sku:
                                # Validate the manually entered SKU
                                if not self._is_valid_sku(actual_manual_sku):
                                    print(f"Skipping invalid manual SKU '{actual_manual_sku}' for '{original_desc}' - not saving to Maestro")
                                    continue
                                selected_sku = actual_manual_sku  # Use the actual SKU, not "MANUAL"
                                source = "UserManualEntry"
                                print(f"Manual SKU entered for '{original_desc}': {selected_sku}")
                            else:
                                print(f"Warning: Manual entry selected but no SKU provided for '{original_desc}'")
                                continue  # Skip this entry if no manual SKU provided
                        else:
                            print(f"Warning: Manual entry selected but no manual_sku_var found for '{original_desc}'")
                            continue  # Skip this entry
                    else:
                        # This is a suggested SKU that was selected
                        # Validate the selected SKU before saving
                        if not self._is_valid_sku(selected_sku):
                            print(f"Skipping invalid suggested SKU '{selected_sku}' for '{original_desc}' - not saving to Maestro")
                            continue

                        is_manual = True
                        for referencia, _ in self.current_suggestions.get(original_desc, []):
                            if referencia == selected_sku:
                                is_manual = False
                                break
                        source = "UserManualEntry" if is_manual else "UserConfirmed"

                    print(f"Selected for '{original_desc}': SKU = {selected_sku} (Source: {source})")

                    part_data = next(
                        (p for p in self.processed_parts if p["original"] == original_desc), None)
                    if part_data:
                        selections_to_save.append({
                            "vin_details": self.vehicle_details,
                            "original_descripcion": part_data["original"],  # Original description
                            "normalized_descripcion": part_data["normalized_expanded"],  # Use expanded for consistency
                            "equivalencia_id": part_data["equivalencia_id"],
                            "confirmed_sku": selected_sku,
                            "source": source
                        })
                else:
                    print(f"Selected for '{original_desc}': None")
            else:
                print(f"No selection variable found for '{original_desc}'")

        if not selections_to_save:
            messagebox.showinfo(
                "Nothing to Save", "No valid SKUs were selected for confirmation.\n\nNote: UNKNOWN selections and invalid SKUs are not saved to preserve data quality.")
            return

        added_count = 0
        skipped_count = 0
        max_id = 0
        if maestro_data_global:
            ids = [entry.get('Maestro_ID', 0) for entry in maestro_data_global if isinstance(
                entry.get('Maestro_ID'), int)]
            if ids:
                max_id = max(ids)
        next_id = max_id + 1

        for selection in selections_to_save:
            is_duplicate = False
            for existing_entry in maestro_data_global:
                # Check for duplicates based on 4-parameter approach
                if (existing_entry.get('maker') == selection['vin_details'].get('maker') and
                    existing_entry.get('model') == selection['vin_details'].get('model') and
                    existing_entry.get('series') == selection['vin_details'].get('series') and
                    existing_entry.get('normalized_descripcion') == selection['normalized_descripcion'] and
                        existing_entry.get('referencia') == selection['confirmed_sku']):
                    is_duplicate = True
                    break
            if not is_duplicate:
                # Extract and convert year to integer
                model = selection['vin_details'].get('model')
                if isinstance(model, (list, tuple, np.ndarray)):
                    model = model[0] if len(model) > 0 else None
                if isinstance(model, str):
                    try:
                        model = int(model)
                    except (ValueError, TypeError):
                        model = None

                new_entry = {
                    'Maestro_ID': next_id,
                    'maker': selection['vin_details'].get('maker'),
                    'model': model,
                    'series': selection['vin_details'].get('series'),
                    'Original_descripcion_Input': selection['original_descripcion'],
                    'Normalized_descripcion_Input': selection['normalized_descripcion'],
                    'Confirmed_referencia': selection['confirmed_sku'],
                    'Source': selection.get('source', 'UserConfirmed'),
                    'Date_Added': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                maestro_data_global.append(new_entry)
                added_count += 1
                next_id += 1
            else:
                skipped_count += 1
                print(
                    f"Skipped duplicate: {selection['original_descripcion']} - {selection['confirmed_sku']}")

        if added_count > 0:
            print(
                f"Attempting to save {added_count} new entries to {DEFAULT_MAESTRO_PATH}...")
            try:
                # Using original consolidado field names with new Maestro column structure
                maestro_columns = [
                    'Maestro_ID', 'maker', 'model',
                    'series', 'Original_descripcion_Input',
                    'Normalized_descripcion_Input', 'Confirmed_referencia',
                    'Source', 'Date_Added'
                ]
                df_to_save = pd.DataFrame(
                    maestro_data_global, columns=maestro_columns)
                df_to_save.to_excel(DEFAULT_MAESTRO_PATH, index=False)
                messagebox.showinfo(
                    "Save Successful", f"{added_count} new confirmation(s) saved to Maestro.xlsx.")
                print(
                    f"Successfully saved {added_count} new entries. Total Maestro entries: {len(maestro_data_global)}")
            except Exception as e:
                messagebox.showerror(
                    "Save Error", f"Failed to write to Maestro.xlsx: {e}")
                print(f"Error writing Maestro.xlsx: {e}")
        elif skipped_count > 0:
            messagebox.showinfo(
                "Already Saved", "The selected confirmations were already present in Maestro.xlsx.")
            print(f"Skipped {skipped_count} duplicate entries.")
        else:
            messagebox.showinfo(
                "Nothing Saved", "No new confirmations were added.")

    # Removed decode_vin_nhtsa


if __name__ == '__main__':
    print("🚀 Starting Fixacar SKU Predictor...")
    print("=" * 50)

    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    print(f"Expected Text_Processing_Rules.xlsx at: {os.path.join(current_dir, DEFAULT_TEXT_PROCESSING_PATH)}")
    print(f"Expected/Creating Maestro.xlsx at: {os.path.join(current_dir, DEFAULT_MAESTRO_PATH)}")
    print(f"Expected fixacar_history.db at: {os.path.join(current_dir, DEFAULT_DB_PATH)}")

    # Check if critical files exist
    critical_files = [
        (DEFAULT_TEXT_PROCESSING_PATH, "Text Processing Rules"),
        (DEFAULT_MAESTRO_PATH, "Maestro Data"),
        (DEFAULT_DB_PATH, "Database")
    ]

    print("\n📁 Checking critical files...")
    for file_path, description in critical_files:
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"✅ {description}: {size_mb:.1f} MB")
        else:
            print(f"⚠️ {description}: NOT FOUND (will be created)")

    print("\n🖥️ Initializing GUI...")
    try:
        root = tk.Tk()
        print("✅ Tkinter root window created")

        root.title("Fixacar SKU Finder v2.0 (with VIN Predictor)")
        root.geometry("1200x800")  # Set a reasonable default size
        print("✅ Window title and size set")

        # Maximize the window on startup to ensure all buttons are visible
        try:
            root.state('zoomed')  # Windows equivalent of maximized
            print("✅ Window maximized")
        except Exception as e:
            print(f"⚠️ Could not maximize window: {e}")

        print("🎨 Creating application interface...")
        app = FixacarApp(root)
        print("✅ Application interface created successfully")

        print("🚀 Starting main event loop...")
        print("=" * 50)
        print("GUI should now be visible!")

        root.mainloop()

    except Exception as e:
        print(f"❌ Error initializing GUI: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)
