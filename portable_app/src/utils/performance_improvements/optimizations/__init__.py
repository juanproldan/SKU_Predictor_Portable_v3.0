"""
Optimizations Module

Provides database and prediction optimizations.
"""

try:
    from .database_optimizer import DatabaseOptimizer
    from .parallel_predictor import ParallelPredictor
    
    __all__ = ['DatabaseOptimizer', 'ParallelPredictor']
    
except ImportError as e:
    print(f"Optimizations not available: {e}")
    __all__ = []
