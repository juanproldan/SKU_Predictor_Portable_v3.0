#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parallel SKU Prediction Module
Implements parallel execution of the 4 prediction sources with smart early termination

Author: Augment Agent
Date: 2025-07-25
"""

import concurrent.futures
import time
from typing import Dict, List, Tuple, Optional, Callable
import threading

class ParallelSKUPredictor:
    """
    Parallel execution manager for the 4 SKU prediction sources:
    1. Maestro Data (highest priority)
    2. Neural Network 
    3. Database/Historical
    4. Fuzzy Matching
    """
    
    def __init__(self, max_workers=4, enable_early_termination=True):
        self.max_workers = max_workers
        self.enable_early_termination = enable_early_termination
        self.prediction_stats = {
            'total_predictions': 0,
            'early_terminations': 0,
            'parallel_executions': 0,
            'average_time_ms': 0
        }
    
    def predict_parallel(self, 
                        make: str, 
                        year: str, 
                        series: str, 
                        descripcion: str,
                        maestro_func: Callable,
                        neural_network_func: Callable,
                        database_func: Callable,
                        fuzzy_func: Callable,
                        **kwargs) -> Dict:
        """
        Execute all 4 prediction sources in parallel with smart early termination
        
        Args:
            make, year, series, description: Vehicle and part info
            maestro_func: Function to call Maestro prediction
            neural_network_func: Function to call NN prediction  
            database_func: Function to call Database prediction
            fuzzy_func: Function to call Fuzzy prediction
            **kwargs: Additional arguments passed to prediction functions
            
        Returns:
            Dict with combined results from all sources
        """
        start_time = time.time()
        self.prediction_stats['total_predictions'] += 1
        
        print(f"🚀 Starting parallel prediction for: {description[:30]}...")
        
        # Check for high-confidence Maestro result first (early termination opportunity)
        if self.enable_early_termination:
            maestro_result = self._try_early_maestro_check(
                make, year, series, description, maestro_func, **kwargs
            )
            if maestro_result and self._is_high_confidence_result(maestro_result):
                end_time = time.time()
                self.prediction_stats['early_terminations'] += 1
                self._update_timing_stats(end_time - start_time)
                
                print(f"  ⚡ Early termination: High-confidence Maestro result ({(end_time - start_time)*1000:.1f}ms)")
                return {
                    'suggestions': maestro_result,
                    'execution_mode': 'early_termination',
                    'sources_used': ['Maestro'],
                    'execution_time_ms': (end_time - start_time) * 1000
                }
        
        # Run all sources in parallel
        return self._execute_parallel_prediction(
            make, year, series, description,
            maestro_func, neural_network_func, database_func, fuzzy_func,
            start_time, **kwargs
        )
    
    def _try_early_maestro_check(self, make: str, year: str, series: str, descripcion: str, 
                                maestro_func: Callable, **kwargs) -> Optional[Dict]:
        """
        Quick Maestro check for early termination
        Only runs if Maestro is expected to be fast
        """
        try:
            # Set a short timeout for early check
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(maestro_func, make, year, series, description, **kwargs)
                try:
                    result = future.result(timeout=0.5)  # 500ms timeout for early check
                    return result
                except concurrent.futures.TimeoutError:
                    # If Maestro takes too long, proceed with parallel execution
                    return None
        except Exception:
            return None
    
    def _is_high_confidence_result(self, result: Dict) -> bool:
        """
        Check if result has high enough confidence for early termination
        """
        if not result or not isinstance(result, dict):
            return False
        
        # Check if we have high-confidence predictions
        suggestions = result.get('suggestions', {})
        if not suggestions:
            return False
        
        # Look for any prediction with confidence >= 0.95
        for referencia, info in suggestions.items():
            confidence = info.get('confidence', 0)
            if confidence >= 0.95:
                print(f"    🎯 High confidence result found: {referencia} ({confidence:.2f})")
                return True
        
        return False
    
    def _execute_parallel_prediction(self, 
                                   make: str, year: str, series: str, descripcion: str,
                                   maestro_func: Callable, neural_network_func: Callable,
                                   database_func: Callable, fuzzy_func: Callable,
                                   start_time: float, **kwargs) -> Dict:
        """Execute all prediction sources in parallel"""
        
        self.prediction_stats['parallel_executions'] += 1
        
        # Prepare prediction tasks
        prediction_tasks = {
            'maestro': (maestro_func, 'Maestro'),
            'neural_network': (neural_network_func, 'Neural Network'),
            'database': (database_func, 'Database'),
            'fuzzy': (fuzzy_func, 'Fuzzy')
        }
        
        results = {}
        execution_times = {}
        
        # Execute all tasks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_source = {}
            for source_name, (func, display_name) in prediction_tasks.items():
                if func:  # Only submit if function is provided
                    future = executor.submit(self._execute_with_timing, func, make, year, series, description, **kwargs)
                    future_to_source[future] = (source_name, display_name)
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_source):
                source_name, display_name = future_to_source[future]
                try:
                    result, exec_time = future.result()
                    results[source_name] = result
                    execution_times[source_name] = exec_time
                    
                    if result:
                        suggestion_count = len(result.get('suggestions', {})) if isinstance(result, dict) else 0
                        print(f"  ✅ {display_name}: {suggestion_count} suggestions ({exec_time:.1f}ms)")
                    else:
                        print(f"  ❌ {display_name}: No results ({exec_time:.1f}ms)")
                        
                except Exception as e:
                    print(f"  ❌ {display_name}: Error - {e}")
                    results[source_name] = None
                    execution_times[source_name] = 0
        
        # Combine results
        combined_suggestions = self._combine_parallel_results(results)
        
        end_time = time.time()
        total_time = end_time - start_time
        self._update_timing_stats(total_time)
        
        print(f"  🏁 Parallel execution completed: {len(combined_suggestions)} total suggestions ({total_time*1000:.1f}ms)")
        
        return {
            'suggestions': combined_suggestions,
            'execution_mode': 'parallel',
            'sources_used': [name for name, result in results.items() if result],
            'execution_time_ms': total_time * 1000,
            'source_times': {name: time_ms for name, time_ms in execution_times.items()},
            'source_results': results
        }
    
    def _execute_with_timing(self, func: Callable, make: str, year: str, series: str, descripcion: str, **kwargs) -> Tuple[Optional[Dict], float]:
        """Execute a prediction function with timing"""
        start_time = time.time()
        try:
            result = func(make, year, series, description, **kwargs)
            end_time = time.time()
            return result, (end_time - start_time) * 1000
        except Exception as e:
            end_time = time.time()
            print(f"    ⚠️ Prediction function error: {e}")
            return None, (end_time - start_time) * 1000
    
    def _combine_parallel_results(self, results: Dict) -> Dict:
        """
        Combine results from all parallel prediction sources
        Maintains the original aggregation logic
        """
        combined_suggestions = {}
        
        # Process results in priority order: Maestro, Neural Network, Database, Fuzzy
        source_priority = ['maestro', 'neural_network', 'database', 'fuzzy']
        
        for source in source_priority:
            if source in results and results[source]:
                source_suggestions = results[source].get('suggestions', {})
                if isinstance(source_suggestions, dict):
                    for referencia, info in source_suggestions.items():
                        if referencia not in combined_suggestions:
                            combined_suggestions[referencia] = info
                        else:
                            # Handle duplicate SKUs - keep higher confidence
                            existing_confidence = combined_suggestions[referencia].get('confidence', 0)
                            new_confidence = info.get('confidence', 0)
                            if new_confidence > existing_confidence:
                                combined_suggestions[referencia] = info
        
        return combined_suggestions
    
    def _update_timing_stats(self, execution_time: float):
        """Update average timing statistics"""
        current_avg = self.prediction_stats['average_time_ms']
        total_predictions = self.prediction_stats['total_predictions']
        
        # Calculate new average
        new_avg = ((current_avg * (total_predictions - 1)) + (execution_time * 1000)) / total_predictions
        self.prediction_stats['average_time_ms'] = new_avg
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics for parallel execution"""
        total = self.prediction_stats['total_predictions']
        early_term_rate = (self.prediction_stats['early_terminations'] / total * 100) if total > 0 else 0
        parallel_rate = (self.prediction_stats['parallel_executions'] / total * 100) if total > 0 else 0
        
        return {
            'total_predictions': total,
            'early_terminations': self.prediction_stats['early_terminations'],
            'parallel_executions': self.prediction_stats['parallel_executions'],
            'early_termination_rate_percent': round(early_term_rate, 2),
            'parallel_execution_rate_percent': round(parallel_rate, 2),
            'average_execution_time_ms': round(self.prediction_stats['average_time_ms'], 2),
            'performance_assessment': self._assess_performance()
        }
    
    def _assess_performance(self) -> str:
        """Assess overall performance based on statistics"""
        avg_time = self.prediction_stats['average_time_ms']
        early_term_rate = (self.prediction_stats['early_terminations'] / 
                          max(1, self.prediction_stats['total_predictions']) * 100)
        
        if avg_time < 500 and early_term_rate > 20:
            return "🚀 EXCELLENT - Fast execution with good early termination"
        elif avg_time < 1000 and early_term_rate > 10:
            return "✅ GOOD - Decent performance with some optimization"
        elif avg_time < 2000:
            return "⚠️ FAIR - Acceptable but could be improved"
        else:
            return "❌ SLOW - Performance optimization needed"
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.prediction_stats = {
            'total_predictions': 0,
            'early_terminations': 0,
            'parallel_executions': 0,
            'average_time_ms': 0
        }
        print("📊 Performance statistics reset")


# Global parallel predictor instance
parallel_predictor = None

def initialize_parallel_predictor(max_workers=4, enable_early_termination=True):
    """Initialize the global parallel predictor"""
    global parallel_predictor
    parallel_predictor = ParallelSKUPredictor(max_workers, enable_early_termination)
    print(f"🚀 Parallel SKU Predictor initialized (workers: {max_workers}, early termination: {enable_early_termination})")
    return parallel_predictor

def get_parallel_predictor():
    """Get the global parallel predictor instance"""
    global parallel_predictor
    if parallel_predictor is None:
        parallel_predictor = initialize_parallel_predictor()
    return parallel_predictor
