"""
Performance Improvements Package

This package provides enhanced functionality for the Fixacar SKU Predictor.
It gracefully handles missing dependencies (like spaCy) and provides fallback implementations.
"""

try:
    from .enhanced_text_processing.smart_text_processor import SmartTextProcessor
    from .enhanced_text_processing.equivalencias_analyzer import EquivalenciasAnalyzer
    from .optimizations.database_optimizer import DatabaseOptimizer
    from .optimizations.parallel_predictor import ParallelPredictor
    
    print("✅ Performance improvements available")
    PERFORMANCE_IMPROVEMENTS_AVAILABLE = True
    
except ImportError as e:
    print(f"⚠️ Performance improvements not available: {e}")
    print("ℹ️ This is normal for packaged executables. Core functionality remains available.")
    PERFORMANCE_IMPROVEMENTS_AVAILABLE = False
    
    # Create dummy classes for compatibility
    class SmartTextProcessor:
        def __init__(self, *args, **kwargs):
            pass
        def process_text(self, text):
            return text
        def is_available(self):
            return False
    
    class EquivalenciasAnalyzer:
        def __init__(self, *args, **kwargs):
            pass
        def analyze_equivalencias(self, *args, **kwargs):
            return {}
        def is_available(self):
            return False
    
    class DatabaseOptimizer:
        def __init__(self, *args, **kwargs):
            pass
        def optimize_database(self, *args, **kwargs):
            pass
        def is_available(self):
            return False
    
    class ParallelPredictor:
        def __init__(self, *args, **kwargs):
            pass
        def predict_parallel(self, *args, **kwargs):
            return []
        def is_available(self):
            return False

# Export all classes
__all__ = [
    'SmartTextProcessor',
    'EquivalenciasAnalyzer', 
    'DatabaseOptimizer',
    'ParallelPredictor',
    'PERFORMANCE_IMPROVEMENTS_AVAILABLE'
]
