#!/usr/bin/env python3
"""
Optimized startup components for faster application loading
"""

import os
import json
import pickle
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

class OptimizedDataLoader:
    """Optimized data loading with caching and lazy loading"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # Use utils/performance_improvements/cache as default
            cache_dir = os.path.join(os.path.dirname(__file__), "performance_improvements", "cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        self._loading_threads = {}
        
    def get_cache_path(self, source_file: str, cache_type: str = "pickle") -> Path:
        """Get cache file path for a source file"""
        source_path = Path(source_file)
        cache_name = f"{source_path.stem}_{cache_type}.cache"
        return self.cache_dir / cache_name
        
    def is_cache_valid(self, source_file: str, cache_file: Path) -> bool:
        """Check if cache is newer than source file"""
        if not cache_file.exists():
            return False
        
        source_path = Path(source_file)
        if not source_path.exists():
            return False
            
        return cache_file.stat().st_mtime > source_path.stat().st_mtime
        
    def load_excel_optimized(self, excel_file: str, force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
        """Load Excel file with caching optimization"""
        cache_file = self.get_cache_path(excel_file, "excel")
        
        # Check cache first
        if not force_refresh and self.is_cache_valid(excel_file, cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Cache read error: {e}, falling back to Excel")
        
        # Load from Excel and cache
        print(f"Loading Excel file: {excel_file}")
        start_time = time.time()
        
        data = pd.read_excel(excel_file, sheet_name=None)
        
        # Cache the data
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Cache write error: {e}")
        
        load_time = (time.time() - start_time) * 1000
        print(f"Excel loaded in {load_time:.1f}ms")
        
        return data
        
    def load_text_processing_rules_optimized(self, excel_file: str) -> Dict[str, Any]:
        """Load and process text processing rules with optimization"""
        cache_file = self.get_cache_path(excel_file, "text_rules")
        
        # Check cache first
        if self.is_cache_valid(excel_file, cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                pass
        
        # Load and process Excel data
        excel_data = self.load_excel_optimized(excel_file)
        
        # Process rules
        rules = {
            'equivalencias': {},
            'abbreviations': {},
            'user_corrections': {}
        }
        
        # Process equivalencias
        if 'Equivalencias' in excel_data:
            equiv_df = excel_data['Equivalencias']
            for _, row in equiv_df.iterrows():
                if pd.notna(row.get('Original')) and pd.notna(row.get('Equivalencia')):
                    rules['equivalencias'][str(row['Original']).lower()] = str(row['Equivalencia']).lower()
        
        # Process abbreviations
        if 'Abbreviations' in excel_data:
            abbr_df = excel_data['Abbreviations']
            for _, row in abbr_df.iterrows():
                if pd.notna(row.get('Abbreviation')) and pd.notna(row.get('Full_Form')):
                    rules['abbreviations'][str(row['Abbreviation']).lower()] = str(row['Full_Form']).lower()
        
        # Process user corrections
        if 'User_Corrections' in excel_data:
            corr_df = excel_data['User_Corrections']
            for _, row in corr_df.iterrows():
                if pd.notna(row.get('Original')) and pd.notna(row.get('Corrected')):
                    rules['user_corrections'][str(row['Original']).lower()] = str(row['Corrected']).lower()
        
        # Cache processed rules
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(rules, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Rules cache write error: {e}")
        
        return rules

class LazySpacyLoader:
    """Lazy loading for spaCy to improve startup time"""
    
    def __init__(self):
        self._nlp = None
        self._loading = False
        self._load_thread = None
        
    def _load_spacy_async(self):
        """Load spaCy in background thread"""
        try:
            import spacy
            self._nlp = spacy.load("es_core_news_sm")
            print("✅ spaCy loaded asynchronously")
        except Exception as e:
            print(f"❌ spaCy async loading failed: {e}")
        finally:
            self._loading = False
    
    def start_loading(self):
        """Start loading spaCy in background"""
        if self._nlp is None and not self._loading:
            self._loading = True
            self._load_thread = threading.Thread(target=self._load_spacy_async, daemon=True)
            self._load_thread.start()
            print("🧠 spaCy loading started in background...")
    
    def get_nlp(self, timeout: float = 30.0) -> Optional[Any]:
        """Get spaCy nlp object, waiting for loading if necessary"""
        if self._nlp is not None:
            return self._nlp
        
        if self._loading and self._load_thread:
            print("⏳ Waiting for spaCy to finish loading...")
            self._load_thread.join(timeout=timeout)
        
        if self._nlp is None:
            print("🧠 Loading spaCy synchronously (fallback)...")
            try:
                import spacy
                self._nlp = spacy.load("es_core_news_sm")
            except Exception as e:
                print(f"❌ spaCy loading failed: {e}")
                return None
        
        return self._nlp
    
    def is_ready(self) -> bool:
        """Check if spaCy is ready to use"""
        return self._nlp is not None

class OptimizedModelLoader:
    """Optimized model loading with compression and caching"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # Use utils/performance_improvements/cache as default
            cache_dir = os.path.join(os.path.dirname(__file__), "performance_improvements", "cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._models = {}
        
    def load_model_optimized(self, model_path: str, model_name: str) -> Any:
        """Load model with optimization"""
        if model_name in self._models:
            return self._models[model_name]
        
        # Check for compressed cache
        cache_file = self.cache_dir / f"{model_name}_compressed.cache"
        
        if cache_file.exists() and self._is_cache_valid(model_path, cache_file):
            try:
                import joblib
                model = joblib.load(cache_file)
                self._models[model_name] = model
                print(f"✅ Loaded {model_name} from compressed cache")
                return model
            except Exception:
                pass
        
        # Load original model
        try:
            import joblib
            model = joblib.load(model_path)
            self._models[model_name] = model
            
            # Create compressed cache
            try:
                joblib.dump(model, cache_file, compress=3)
            except Exception as e:
                print(f"Model cache write error: {e}")
            
            print(f"✅ Loaded {model_name} from original file")
            return model
            
        except Exception as e:
            print(f"❌ Failed to load {model_name}: {e}")
            return None
    
    def _is_cache_valid(self, source_file: str, cache_file: Path) -> bool:
        """Check if cache is valid"""
        source_path = Path(source_file)
        if not source_path.exists():
            return False
        return cache_file.stat().st_mtime > source_path.stat().st_mtime

class FastTextProcessor:
    """Fast text processing without heavy dependencies"""
    
    def __init__(self, rules: Dict[str, Any]):
        self.equivalencias = rules.get('equivalencias', {})
        self.abbreviations = rules.get('abbreviations', {})
        self.user_corrections = rules.get('user_corrections', {})
        
        # Pre-compile common patterns for speed
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for common transformations"""
        import re
        
        # Common automotive abbreviations
        self.abbr_patterns = []
        for abbr, full in self.abbreviations.items():
            # Word boundary pattern for accurate replacement
            pattern = re.compile(r'\b' + re.escape(abbr) + r'\b', re.IGNORECASE)
            self.abbr_patterns.append((pattern, full))
    
    def process_fast(self, text: str) -> str:
        """Fast text processing without spaCy"""
        if not text:
            return text
        
        # Normalize
        result = text.lower().strip()
        
        # Apply user corrections first (highest priority)
        for orig, corrected in self.user_corrections.items():
            if orig in result:
                result = result.replace(orig, corrected)
        
        # Apply abbreviations
        for pattern, replacement in self.abbr_patterns:
            result = pattern.sub(replacement, result)
        
        # Apply equivalencias
        for orig, equiv in self.equivalencias.items():
            if orig in result:
                result = result.replace(orig, equiv)
        
        return result.strip()

# Global instances for reuse
_data_loader = None
_spacy_loader = None
_model_loader = None
_text_processor = None

def get_data_loader() -> OptimizedDataLoader:
    """Get global data loader instance"""
    global _data_loader
    if _data_loader is None:
        _data_loader = OptimizedDataLoader()
    return _data_loader

def get_spacy_loader() -> LazySpacyLoader:
    """Get global spaCy loader instance"""
    global _spacy_loader
    if _spacy_loader is None:
        _spacy_loader = LazySpacyLoader()
    return _spacy_loader

def get_model_loader() -> OptimizedModelLoader:
    """Get global model loader instance"""
    global _model_loader
    if _model_loader is None:
        _model_loader = OptimizedModelLoader()
    return _model_loader

def get_text_processor(rules: Dict[str, Any] = None) -> FastTextProcessor:
    """Get global text processor instance"""
    global _text_processor
    if _text_processor is None and rules:
        _text_processor = FastTextProcessor(rules)
    return _text_processor

def initialize_optimizations():
    """Initialize all optimizations"""
    print("🚀 Initializing performance optimizations...")
    
    # Start spaCy loading in background
    spacy_loader = get_spacy_loader()
    spacy_loader.start_loading()
    
    # Initialize other components
    get_data_loader()
    get_model_loader()
    
    print("✅ Performance optimizations initialized")
