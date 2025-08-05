"""
Enhanced Text Processing Module

Provides advanced text processing capabilities using spaCy when available.
"""

try:
    from .smart_text_processor import SmartTextProcessor
    from .equivalencias_analyzer import EquivalenciasAnalyzer
    
    __all__ = ['SmartTextProcessor', 'EquivalenciasAnalyzer']
    
except ImportError as e:
    print(f"Enhanced text processing not available: {e}")
    __all__ = []
