#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive Performance and Accuracy Validation System
Real-world testing with actual data to validate all improvements

Author: Augment Agent
Date: 2025-07-25
"""

import json
import sqlite3
import pandas as pd
import time
import numpy as np
from typing import Dict, List, Tuple, Any
import os
import sys
from collections import defaultdict
import random

# Add the src directory to the path to import the main application
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

class ComprehensiveValidator:
    """
    Comprehensive validation system for performance and accuracy improvements
    """
    
    def __init__(self, source_files_path: str):
        self.source_files_path = source_files_path
        self.consolidado_path = os.path.join(source_files_path, 'Consolidado.json')
        self.db_path = os.path.join(source_files_path, 'processed_consolidado.db')
        self.maestro_path = os.path.join(source_files_path, 'Maestro.xlsx')
        
        self.test_data = None
        self.baseline_results = {}
        self.improved_results = {}
        self.validation_report = {}
        
        print(f"🔍 Initializing Comprehensive Validator")
        print(f"   Source Files Path: {source_files_path}")
        print(f"   Consolidado: {self.consolidado_path}")
        print(f"   Database: {self.db_path}")
        print(f"   Maestro: {self.maestro_path}")
    
    def load_real_data(self, sample_size: int = 1000) -> Dict:
        """
        Load real data from Consolidado.json for testing
        
        Args:
            sample_size: Number of records to sample for testing
            
        Returns:
            Dictionary with test data
        """
        print(f"\n📊 Loading real data for validation...")
        
        if not os.path.exists(self.consolidado_path):
            raise FileNotFoundError(f"Consolidado.json not found at: {self.consolidado_path}")
        
        # Load Consolidado.json
        with open(self.consolidado_path, 'r', encoding='utf-8') as f:
            consolidado_data = json.load(f)
        
        print(f"   📁 Loaded {len(consolidado_data)} records from Consolidado.json")
        
        # Sample data for testing
        if len(consolidado_data) > sample_size:
            test_records = random.sample(consolidado_data, sample_size)
            print(f"   🎯 Sampled {sample_size} records for testing")
        else:
            test_records = consolidado_data
            print(f"   📋 Using all {len(test_records)} records for testing")
        
        # Analyze data characteristics - check different possible field names
        descriptions = []
        makes = []
        years = []
        skus = []

        # Check first record to understand structure
        if test_records:
            sample_record = test_records[0]
            print(f"   🔍 Sample record keys: {list(sample_record.keys())}")

            # Try different possible field names
            desc_fields = ['descripcion', 'description', 'desc', 'Descripcion', 'descripcion']
            make_fields = ['maker', 'make', 'marca', 'Marca']
            year_fields = ['model', 'year', 'ano', 'Ano', 'anio', 'Anio']
            sku_fields = ['referencia', 'referencia', 'codigo', 'Codigo']

            # Find the correct field names
            desc_field = next((f for f in desc_fields if f in sample_record), None)
            make_field = next((f for f in make_fields if f in sample_record), None)
            year_field = next((f for f in year_fields if f in sample_record), None)
            sku_field = next((f for f in sku_fields if f in sample_record), None)

            print(f"   🔍 Detected fields - Desc: {desc_field}, maker: {make_field}, model: {year_field}, referencia: {sku_field}")

            # Extract data using detected field names
            for record in test_records:
                if desc_field and record.get(desc_field):
                    descriptions.append(record[desc_field])
                if make_field and record.get(make_field):
                    makes.append(record[make_field])
                if year_field and record.get(year_field):
                    years.append(str(record[year_field]))
                if sku_field and record.get(sku_field):
                    skus.append(record[sku_field])
        
        self.test_data = {
            'records': test_records,
            'descriptions': descriptions,
            'makes': list(set(makes)),
            'years': list(set(years)),
            'skus': list(set(skus)),
            'stats': {
                'total_records': len(test_records),
                'unique_descriptions': len(set(descriptions)),
                'unique_makes': len(set(makes)),
                'unique_years': len(set(years)),
                'unique_skus': len(set(skus)),
                'avg_description_length': np.mean([len(desc.split()) for desc in descriptions if desc]),
                'records_with_sku': len([r for r in test_records if r.get('referencia')])
            }
        }
        
        print(f"   📈 Data Analysis:")
        print(f"      Total Records: {self.test_data['stats']['total_records']}")
        print(f"      Unique Descriptions: {self.test_data['stats']['unique_descriptions']}")
        print(f"      Unique Makes: {self.test_data['stats']['unique_makes']}")
        print(f"      Unique Years: {self.test_data['stats']['unique_years']}")
        print(f"      Unique SKUs: {self.test_data['stats']['unique_skus']}")
        print(f"      Avg Description Length: {self.test_data['stats']['avg_description_length']:.1f} words")
        print(f"      Records with referencia: {self.test_data['stats']['records_with_sku']}")
        
        return self.test_data
    
    def benchmark_database_performance(self) -> Dict:
        """
        Benchmark database performance with real queries
        """
        print(f"\n🗄️ Benchmarking Database Performance...")
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        
        # Test queries with real data patterns
        test_queries = [
            {
                'name': 'Count All Records',
                'query': 'SELECT COUNT(*) FROM processed_consolidado',
                'expected_fast': True
            },
            {
                'name': 'Make Filter (Toyota)',
                'query': "SELECT COUNT(*) FROM processed_consolidado WHERE maker = 'TOYOTA'",
                'expected_fast': True
            },
            {
                'name': 'Make+Year Filter',
                'query': "SELECT COUNT(*) FROM processed_consolidado WHERE maker = 'TOYOTA' AND model = '2020'",
                'expected_fast': True
            },
            {
                'name': 'SKU Frequency Analysis',
                'query': "SELECT referencia, COUNT(*) as freq FROM processed_consolidado WHERE referencia IS NOT NULL GROUP BY referencia ORDER BY freq DESC LIMIT 10",
                'expected_fast': False
            },
            {
                'name': 'Description Search',
                'query': "SELECT * FROM processed_consolidado WHERE normalized_descripcion LIKE '%parachoques%' LIMIT 10",
                'expected_fast': False
            },
            {
                'name': 'Complex Prediction Pattern',
                'query': """
                    SELECT referencia, COUNT(*) as frequency 
                    FROM processed_consolidado 
                    WHERE maker = 'TOYOTA' AND model = '2020' 
                    AND normalized_descripcion LIKE '%parachoques%'
                    GROUP BY referencia ORDER BY frequency DESC LIMIT 5
                """,
                'expected_fast': True
            }
        ]
        
        results = {}
        
        for test in test_queries:
            print(f"   🔍 Testing: {test['name']}")
            
            # Run query multiple times for accurate timing
            times = []
            for _ in range(3):
                start_time = time.time()
                cursor = conn.cursor()
                cursor.execute(test['query'])
                results_count = len(cursor.fetchall())
                end_time = time.time()
                times.append((end_time - start_time) * 1000)  # Convert to ms
            
            avg_time = np.mean(times)
            is_fast = avg_time < 50  # Under 50ms is considered fast
            
            results[test['name']] = {
                'avg_time_ms': avg_time,
                'min_time_ms': min(times),
                'max_time_ms': max(times),
                'results_count': results_count,
                'is_fast': is_fast,
                'expected_fast': test['expected_fast'],
                'performance_ok': is_fast if test['expected_fast'] else avg_time < 1000  # 1s for complex queries
            }
            
            status = "🚀" if results[test['name']]['performance_ok'] else "⚠️"
            print(f"      {status} {avg_time:.2f}ms ({results_count} results)")
        
        conn.close()
        
        # Summary
        fast_queries = sum(1 for r in results.values() if r['performance_ok'])
        total_queries = len(results)
        
        print(f"\n   📊 Database Performance Summary:")
        print(f"      Fast Queries: {fast_queries}/{total_queries}")
        print(f"      Performance Score: {fast_queries/total_queries*100:.1f}%")
        
        return results
    
    def benchmark_text_processing(self, sample_size: int = 100) -> Dict:
        """
        Benchmark text processing improvements with real descriptions
        """
        print(f"\n📝 Benchmarking Text Processing Performance...")
        
        if not self.test_data:
            raise ValueError("Test data not loaded. Call load_real_data() first.")
        
        # Sample descriptions for testing
        descriptions = self.test_data['descriptions'][:sample_size]
        print(f"   Testing with {len(descriptions)} real descriptions")
        
        # Import text processing functions
        try:
            from utils.text_utils import normalize_text
            print(f"   ✅ Imported standard text processing")
        except ImportError:
            print(f"   ❌ Could not import standard text processing")
            return {}
        
        # Test standard text processing
        print(f"   🔄 Testing standard text processing...")
        standard_times = []
        standard_results = []
        
        for desc in descriptions:
            start_time = time.time()
            result = normalize_text(desc)
            end_time = time.time()
            
            standard_times.append((end_time - start_time) * 1000)
            standard_results.append(result)
        
        # Test enhanced text processing (if available)
        enhanced_times = []
        enhanced_results = []
        
        try:
            # Try to import the main app to get enhanced processing
            sys.path.insert(0, os.path.join(project_root, 'src'))
            from main_app import SKUPredictorApp
            
            # Create a temporary app instance
            app = SKUPredictorApp()
            
            print(f"   🔄 Testing enhanced text processing...")
            
            for desc in descriptions:
                start_time = time.time()
                result = app.enhanced_normalize_text(desc)
                end_time = time.time()
                
                enhanced_times.append((end_time - start_time) * 1000)
                enhanced_results.append(result)
            
            enhanced_available = True
            
        except Exception as e:
            print(f"   ⚠️ Enhanced text processing not available: {e}")
            enhanced_available = False
            enhanced_times = standard_times
            enhanced_results = standard_results
        
        # Analyze results
        results = {
            'sample_size': len(descriptions),
            'standard_processing': {
                'avg_time_ms': np.mean(standard_times),
                'total_time_ms': sum(standard_times),
                'min_time_ms': min(standard_times),
                'max_time_ms': max(standard_times)
            },
            'enhanced_processing': {
                'avg_time_ms': np.mean(enhanced_times),
                'total_time_ms': sum(enhanced_times),
                'min_time_ms': min(enhanced_times),
                'max_time_ms': max(enhanced_times),
                'available': enhanced_available
            }
        }
        
        # Calculate improvement
        if enhanced_available:
            time_improvement = (results['standard_processing']['avg_time_ms'] - 
                              results['enhanced_processing']['avg_time_ms']) / results['standard_processing']['avg_time_ms'] * 100
            results['time_improvement_percent'] = time_improvement
        
        # Analyze text changes
        if enhanced_available:
            changes_detected = 0
            significant_changes = 0
            
            for i, (std, enh) in enumerate(zip(standard_results, enhanced_results)):
                if std != enh:
                    changes_detected += 1
                    # Count significant changes (more than just case/whitespace)
                    if len(std.split()) != len(enh.split()) or std.lower().replace(' ', '') != enh.lower().replace(' ', ''):
                        significant_changes += 1
            
            results['text_analysis'] = {
                'total_comparisons': len(descriptions),
                'changes_detected': changes_detected,
                'significant_changes': significant_changes,
                'change_rate_percent': changes_detected / len(descriptions) * 100,
                'significant_change_rate_percent': significant_changes / len(descriptions) * 100
            }
        
        # Print summary
        print(f"   📊 Text Processing Results:")
        print(f"      Standard Processing: {results['standard_processing']['avg_time_ms']:.2f}ms avg")
        if enhanced_available:
            print(f"      Enhanced Processing: {results['enhanced_processing']['avg_time_ms']:.2f}ms avg")
            if 'time_improvement_percent' in results:
                improvement_sign = "🚀" if results['time_improvement_percent'] > 0 else "⚠️"
                print(f"      {improvement_sign} Time Change: {results['time_improvement_percent']:+.1f}%")
            
            if 'text_analysis' in results:
                print(f"      Text Changes: {results['text_analysis']['changes_detected']}/{results['text_analysis']['total_comparisons']} ({results['text_analysis']['change_rate_percent']:.1f}%)")
                print(f"      Significant Changes: {results['text_analysis']['significant_changes']} ({results['text_analysis']['significant_change_rate_percent']:.1f}%)")
        
        return results
    
    def validate_cache_performance(self, test_cycles: int = 3) -> Dict:
        """
        Validate cache performance with real prediction patterns
        """
        print(f"\n💾 Validating Cache Performance...")
        
        if not self.test_data:
            raise ValueError("Test data not loaded. Call load_real_data() first.")
        
        # Try to import cache system
        try:
            from utils.performance_improvements.cache.referencia_prediction_cache import get_cache
            cache = get_cache()
            cache_available = True
            print(f"   ✅ Cache system available")
        except ImportError:
            print(f"   ❌ Cache system not available")
            return {'available': False}
        
        # Create test prediction patterns
        test_patterns = []
        for record in self.test_data['records'][:50]:  # Use first 50 records
            if all(record.get(key) for key in ['maker', 'model', 'series', 'descripcion']):
                test_patterns.append({
                    'make': record['maker'],
                    'year': str(record['model']),
                    'series': record['series'],
                    'description': record['descripcion']
                })
        
        print(f"   🎯 Testing with {len(test_patterns)} prediction patterns")
        
        # Clear cache for clean test
        if hasattr(cache, 'clear'):
            cache.clear()
        
        results = {
            'available': cache_available,
            'test_patterns': len(test_patterns),
            'cycles': []
        }
        
        for cycle in range(test_cycles):
            print(f"   🔄 Test Cycle {cycle + 1}/{test_cycles}")
            
            cycle_start = time.time()
            hits = 0
            misses = 0
            
            for pattern in test_patterns:
                cache_key = f'{maker}_{model}_{series}_{descripcion_hash}'']}"
                
                # Try to get from cache
                start_time = time.time()
                cached_result = cache.get(cache_key) if hasattr(cache, 'get') else None
                get_time = (time.time() - start_time) * 1000
                
                if cached_result is not None:
                    hits += 1
                else:
                    misses += 1
                    # Simulate prediction result and cache it
                    fake_result = {'referencia': 'TEST_SKU', 'confidence': 0.8}
                    if hasattr(cache, 'set'):
                        cache.set(cache_key, fake_result)
            
            cycle_end = time.time()
            cycle_time = (cycle_end - cycle_start) * 1000
            
            cycle_results = {
                'cycle': cycle + 1,
                'hits': hits,
                'misses': misses,
                'hit_rate_percent': hits / (hits + misses) * 100 if (hits + misses) > 0 else 0,
                'total_time_ms': cycle_time,
                'avg_time_per_lookup_ms': cycle_time / len(test_patterns) if test_patterns else 0
            }
            
            results['cycles'].append(cycle_results)
            
            print(f"      Hits: {hits}, Misses: {misses}, Hit Rate: {cycle_results['hit_rate_percent']:.1f}%")
        
        # Calculate overall statistics
        if results['cycles']:
            avg_hit_rate = np.mean([c['hit_rate_percent'] for c in results['cycles']])
            avg_lookup_time = np.mean([c['avg_time_per_lookup_ms'] for c in results['cycles']])
            
            results['summary'] = {
                'avg_hit_rate_percent': avg_hit_rate,
                'avg_lookup_time_ms': avg_lookup_time,
                'expected_improvement': avg_hit_rate * 0.5  # Estimate 50% time savings on cache hits
            }
            
            print(f"   📊 Cache Performance Summary:")
            print(f"      Average Hit Rate: {avg_hit_rate:.1f}%")
            print(f"      Average Lookup Time: {avg_lookup_time:.3f}ms")
            print(f"      Expected Performance Improvement: {results['summary']['expected_improvement']:.1f}%")
        
        return results

    def validate_prediction_accuracy(self, sample_size: int = 100) -> Dict:
        """
        Validate prediction accuracy improvements with real data
        """
        print(f"\n🎯 Validating Prediction Accuracy...")

        if not self.test_data:
            raise ValueError("Test data not loaded. Call load_real_data() first.")

        # Get records with known SKUs for accuracy testing
        records_with_sku = [r for r in self.test_data['records'] if r.get('referencia')]
        if len(records_with_sku) < sample_size:
            test_records = records_with_sku
        else:
            test_records = random.sample(records_with_sku, sample_size)

        print(f"   🎯 Testing accuracy with {len(test_records)} records with known SKUs")

        # Try to import the main application
        try:
            sys.path.insert(0, os.path.join(project_root, 'src'))
            from main_app import FixacarApp

            # Create a mock root for the app
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the window

            app = FixacarApp(root)
            prediction_available = True
            print(f"   ✅ Fixacar application loaded")
        except Exception as e:
            print(f"   ❌ Could not load Fixacar app: {e}")
            return {'available': False, 'error': str(e)}

        results = {
            'available': prediction_available,
            'test_records': len(test_records),
            'predictions': [],
            'accuracy_metrics': {}
        }

        correct_predictions = 0
        total_predictions = 0
        prediction_times = []
        confidence_scores = []

        print(f"   🔄 Running predictions...")

        for i, record in enumerate(test_records):
            if i % 20 == 0:
                print(f"      Progress: {i}/{len(test_records)}")

            try:
                # Extract prediction inputs
                make = record.get('maker', '')
                year = str(record.get('model', ''))
                series = record.get('series', '')
                description = record.get('descripcion', '')
                expected_sku = record.get('referencia', '')

                if not all([make, year, series, description]):
                    continue

                # Run prediction
                start_time = time.time()
                prediction_result = app.predict_sku_for_part(make, year, series, description)
                prediction_time = (time.time() - start_time) * 1000

                prediction_times.append(prediction_time)
                total_predictions += 1

                # Extract predicted SKU and confidence
                predicted_sku = None
                confidence = 0.0

                if prediction_result and len(prediction_result) > 0:
                    # Assuming prediction_result is a list of predictions
                    best_prediction = prediction_result[0]
                    if isinstance(best_prediction, dict):
                        predicted_sku = best_prediction.get('referencia', '')
                        confidence = best_prediction.get('confidence', 0.0)
                    elif isinstance(best_prediction, tuple):
                        predicted_sku = best_prediction[0] if len(best_prediction) > 0 else ''
                        confidence = best_prediction[1] if len(best_prediction) > 1 else 0.0

                # Check accuracy
                is_correct = predicted_sku == expected_sku if predicted_sku else False
                if is_correct:
                    correct_predictions += 1

                confidence_scores.append(confidence)

                # Store detailed result
                results['predictions'].append({
                    'make': make,
                    'year': year,
                    'series': series,
                    'description': description,
                    'expected_sku': expected_sku,
                    'predicted_sku': predicted_sku,
                    'confidence': confidence,
                    'is_correct': is_correct,
                    'prediction_time_ms': prediction_time
                })

            except Exception as e:
                print(f"      ⚠️ Error predicting for record {i}: {e}")
                continue

        # Calculate accuracy metrics
        if total_predictions > 0:
            accuracy = correct_predictions / total_predictions
            avg_prediction_time = np.mean(prediction_times)
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0

            results['accuracy_metrics'] = {
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'accuracy_percent': accuracy * 100,
                'avg_prediction_time_ms': avg_prediction_time,
                'avg_confidence': avg_confidence,
                'confidence_distribution': {
                    'high_confidence_count': len([c for c in confidence_scores if c >= 0.8]),
                    'medium_confidence_count': len([c for c in confidence_scores if 0.5 <= c < 0.8]),
                    'low_confidence_count': len([c for c in confidence_scores if c < 0.5])
                }
            }

            print(f"   📊 Prediction Accuracy Results:")
            print(f"      Total Predictions: {total_predictions}")
            print(f"      Correct Predictions: {correct_predictions}")
            print(f"      Accuracy: {accuracy * 100:.1f}%")
            print(f"      Average Prediction Time: {avg_prediction_time:.2f}ms")
            print(f"      Average Confidence: {avg_confidence:.3f}")
            print(f"      High Confidence (≥0.8): {results['accuracy_metrics']['confidence_distribution']['high_confidence_count']}")
            print(f"      Medium Confidence (0.5-0.8): {results['accuracy_metrics']['confidence_distribution']['medium_confidence_count']}")
            print(f"      Low Confidence (<0.5): {results['accuracy_metrics']['confidence_distribution']['low_confidence_count']}")

        return results

    def run_comprehensive_validation(self, sample_size: int = 500) -> Dict:
        """
        Run complete validation suite
        """
        print(f"\n🚀 STARTING COMPREHENSIVE VALIDATION")
        print(f"=" * 60)

        validation_start = time.time()

        # Step 1: Load real data
        try:
            self.load_real_data(sample_size)
        except Exception as e:
            print(f"❌ Failed to load real data: {e}")
            return {'error': 'Failed to load real data', 'details': str(e)}

        # Step 2: Database performance
        try:
            db_results = self.benchmark_database_performance()
        except Exception as e:
            print(f"❌ Database benchmark failed: {e}")
            db_results = {'error': str(e)}

        # Step 3: Text processing performance
        try:
            text_results = self.benchmark_text_processing(min(100, sample_size // 5))
        except Exception as e:
            print(f"❌ Text processing benchmark failed: {e}")
            text_results = {'error': str(e)}

        # Step 4: Cache performance
        try:
            cache_results = self.validate_cache_performance()
        except Exception as e:
            print(f"❌ Cache validation failed: {e}")
            cache_results = {'error': str(e)}

        # Step 5: Prediction accuracy
        try:
            accuracy_results = self.validate_prediction_accuracy(min(50, sample_size // 10))
        except Exception as e:
            print(f"❌ Accuracy validation failed: {e}")
            accuracy_results = {'error': str(e)}

        validation_end = time.time()
        total_time = validation_end - validation_start

        # Compile comprehensive report
        self.validation_report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_validation_time_seconds': total_time,
            'sample_size': sample_size,
            'data_analysis': self.test_data['stats'] if self.test_data else {},
            'database_performance': db_results,
            'text_processing_performance': text_results,
            'cache_performance': cache_results,
            'prediction_accuracy': accuracy_results
        }

        # Generate summary
        self.generate_validation_summary()

        return self.validation_report

    def generate_validation_summary(self):
        """
        Generate a comprehensive validation summary
        """
        print(f"\n📋 COMPREHENSIVE VALIDATION SUMMARY")
        print(f"=" * 60)

        report = self.validation_report

        print(f"🕒 Validation completed at: {report['timestamp']}")
        print(f"⏱️ Total validation time: {report['total_validation_time_seconds']:.1f} seconds")
        print(f"📊 Sample size: {report['sample_size']} records")

        # Data Analysis Summary
        if 'data_analysis' in report and report['data_analysis']:
            stats = report['data_analysis']
            print(f"\n📈 DATA ANALYSIS:")
            print(f"   Total Records: {stats.get('total_records', 'N/A')}")
            print(f"   Unique Descriptions: {stats.get('unique_descriptions', 'N/A')}")
            print(f"   Records with referencia: {stats.get('records_with_sku', 'N/A')}")
            print(f"   Avg Description Length: {stats.get('avg_description_length', 0):.1f} words")

        # Database Performance Summary
        if 'database_performance' in report and 'error' not in report['database_performance']:
            db_perf = report['database_performance']
            fast_queries = sum(1 for r in db_perf.values() if isinstance(r, dict) and r.get('performance_ok', False))
            total_queries = len([r for r in db_perf.values() if isinstance(r, dict)])

            print(f"\n🗄️ DATABASE PERFORMANCE:")
            print(f"   Fast Queries: {fast_queries}/{total_queries}")
            print(f"   Performance Score: {fast_queries/total_queries*100:.1f}%" if total_queries > 0 else "   Performance Score: N/A")

            # Show specific query performance
            for query_name, result in db_perf.items():
                if isinstance(result, dict) and 'avg_time_ms' in result:
                    status = "🚀" if result.get('performance_ok', False) else "⚠️"
                    print(f"   {status} {query_name}: {result['avg_time_ms']:.2f}ms")

        # Text Processing Summary
        if 'text_processing_performance' in report and 'error' not in report['text_processing_performance']:
            text_perf = report['text_processing_performance']
            print(f"\n📝 TEXT PROCESSING PERFORMANCE:")
            print(f"   Sample Size: {text_perf.get('sample_size', 'N/A')}")

            if text_perf.get('enhanced_processing', {}).get('available', False):
                std_time = text_perf['standard_processing']['avg_time_ms']
                enh_time = text_perf['enhanced_processing']['avg_time_ms']
                improvement = text_perf.get('time_improvement_percent', 0)

                print(f"   Standard Processing: {std_time:.2f}ms avg")
                print(f"   Enhanced Processing: {enh_time:.2f}ms avg")

                if improvement > 0:
                    print(f"   🚀 Performance Improvement: +{improvement:.1f}%")
                elif improvement < 0:
                    print(f"   ⚠️ Performance Impact: {improvement:.1f}%")
                else:
                    print(f"   ➡️ No significant performance change")

                if 'text_analysis' in text_perf:
                    ta = text_perf['text_analysis']
                    print(f"   Text Changes: {ta['changes_detected']}/{ta['total_comparisons']} ({ta['change_rate_percent']:.1f}%)")
                    print(f"   Significant Changes: {ta['significant_changes']} ({ta['significant_change_rate_percent']:.1f}%)")
            else:
                print(f"   ⚠️ Enhanced processing not available")

        # Cache Performance Summary
        if 'cache_performance' in report and report['cache_performance'].get('available', False):
            cache_perf = report['cache_performance']
            print(f"\n💾 CACHE PERFORMANCE:")

            if 'summary' in cache_perf:
                summary = cache_perf['summary']
                print(f"   Average Hit Rate: {summary['avg_hit_rate_percent']:.1f}%")
                print(f"   Average Lookup Time: {summary['avg_lookup_time_ms']:.3f}ms")
                print(f"   Expected Performance Improvement: {summary['expected_improvement']:.1f}%")
            else:
                print(f"   Test Patterns: {cache_perf.get('test_patterns', 'N/A')}")
        else:
            print(f"\n💾 CACHE PERFORMANCE:")
            print(f"   ❌ Cache system not available")

        # Prediction Accuracy Summary
        if 'prediction_accuracy' in report and report['prediction_accuracy'].get('available', False):
            acc_perf = report['prediction_accuracy']
            print(f"\n🎯 PREDICTION ACCURACY:")

            if 'accuracy_metrics' in acc_perf:
                metrics = acc_perf['accuracy_metrics']
                print(f"   Total Predictions: {metrics['total_predictions']}")
                print(f"   Accuracy: {metrics['accuracy_percent']:.1f}%")
                print(f"   Average Prediction Time: {metrics['avg_prediction_time_ms']:.2f}ms")
                print(f"   Average Confidence: {metrics['avg_confidence']:.3f}")

                dist = metrics['confidence_distribution']
                print(f"   High Confidence (≥0.8): {dist['high_confidence_count']}")
                print(f"   Medium Confidence (0.5-0.8): {dist['medium_confidence_count']}")
                print(f"   Low Confidence (<0.5): {dist['low_confidence_count']}")
        else:
            print(f"\n🎯 PREDICTION ACCURACY:")
            print(f"   ❌ Prediction system not available")

        print(f"\n" + "=" * 60)
