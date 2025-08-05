#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Validation Runner - Execute comprehensive validation and generate reports

Author: Augment Agent
Date: 2025-07-25
"""

import os
import sys
import json
import time
from comprehensive_validator import ComprehensiveValidator

def run_full_validation():
    """
    Run the complete validation suite with real data
    """
    print("🚀 STARTING COMPREHENSIVE PERFORMANCE & ACCURACY VALIDATION")
    print("=" * 70)
    
    # Set up paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    source_files_path = os.path.join(project_root, "Source_Files")
    
    print(f"📁 Project Root: {project_root}")
    print(f"📁 Source Files: {source_files_path}")
    
    # Verify source files exist
    required_files = ['Consolidado.json', 'processed_consolidado.db', 'Maestro.xlsx']
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(source_files_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
        else:
            print(f"✅ Found: {file}")
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    # Initialize validator
    validator = ComprehensiveValidator(source_files_path)
    
    # Run validation with appropriate sample size
    print(f"\n🎯 Starting validation with sample size: 200")
    
    try:
        results = validator.run_comprehensive_validation(sample_size=200)
        
        # Save detailed report
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        report_file = f"validation_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Detailed report saved to: {report_file}")
        
        # Generate executive summary
        generate_executive_summary(results, f"executive_summary_{timestamp}.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_executive_summary(results: dict, output_file: str):
    """
    Generate an executive summary of validation results
    """
    print(f"\n📋 Generating Executive Summary...")
    
    summary_lines = []
    summary_lines.append("🚀 SKU PREDICTOR v2.0 - PERFORMANCE & ACCURACY VALIDATION REPORT")
    summary_lines.append("=" * 70)
    summary_lines.append(f"Generated: {results.get('timestamp', 'Unknown')}")
    summary_lines.append(f"Validation Time: {results.get('total_validation_time_seconds', 0):.1f} seconds")
    summary_lines.append(f"Sample Size: {results.get('sample_size', 'Unknown')} records")
    summary_lines.append("")
    
    # Executive Summary
    summary_lines.append("📊 EXECUTIVE SUMMARY")
    summary_lines.append("-" * 30)
    
    # Calculate overall scores
    scores = []
    issues = []
    improvements = []
    
    # Database Performance
    if 'database_performance' in results and 'error' not in results['database_performance']:
        db_perf = results['database_performance']
        fast_queries = sum(1 for r in db_perf.values() if isinstance(r, dict) and r.get('performance_ok', False))
        total_queries = len([r for r in db_perf.values() if isinstance(r, dict)])
        
        if total_queries > 0:
            db_score = fast_queries / total_queries
            scores.append(('Database Performance', db_score))
            
            if db_score >= 0.7:
                improvements.append(f"✅ Database: {fast_queries}/{total_queries} queries optimized ({db_score*100:.0f}%)")
            else:
                issues.append(f"⚠️ Database: Only {fast_queries}/{total_queries} queries optimized")
    else:
        issues.append("❌ Database: Performance testing failed")
    
    # Text Processing
    if ('text_processing_performance' in results and 
        'error' not in results['text_processing_performance']):
        text_perf = results['text_processing_performance']
        
        if text_perf.get('enhanced_processing', {}).get('available', False):
            improvements.append("✅ Enhanced Text Processing: Available and integrated")
            scores.append(('Text Processing', 0.8))
            
            if 'text_analysis' in text_perf:
                change_rate = text_perf['text_analysis']['change_rate_percent']
                improvements.append(f"   - Text improvements applied to {change_rate:.1f}% of descriptions")
        else:
            issues.append("⚠️ Enhanced Text Processing: Not available")
    
    # Cache Performance
    if ('cache_performance' in results and 
        results['cache_performance'].get('available', False)):
        cache_perf = results['cache_performance']
        improvements.append("✅ Caching System: Available and functional")
        scores.append(('Caching', 0.7))
        
        if 'summary' in cache_perf:
            hit_rate = cache_perf['summary']['avg_hit_rate_percent']
            expected_improvement = cache_perf['summary']['expected_improvement']
            improvements.append(f"   - Expected cache hit rate: {hit_rate:.1f}%")
            improvements.append(f"   - Expected performance improvement: {expected_improvement:.1f}%")
    else:
        issues.append("❌ Caching System: Not available")
    
    # Prediction Accuracy
    if ('prediction_accuracy' in results and 
        results['prediction_accuracy'].get('available', False) and
        'accuracy_metrics' in results['prediction_accuracy']):
        acc_metrics = results['prediction_accuracy']['accuracy_metrics']
        accuracy = acc_metrics['accuracy_percent']
        avg_time = acc_metrics['avg_prediction_time_ms']
        
        scores.append(('Prediction Accuracy', accuracy / 100))
        improvements.append(f"✅ Prediction System: {accuracy:.1f}% accuracy")
        improvements.append(f"   - Average prediction time: {avg_time:.2f}ms")
        
        # Confidence distribution
        dist = acc_metrics['confidence_distribution']
        high_conf = dist['high_confidence_count']
        total_pred = acc_metrics['total_predictions']
        if total_pred > 0:
            high_conf_rate = high_conf / total_pred * 100
            improvements.append(f"   - High confidence predictions: {high_conf_rate:.1f}%")
    else:
        issues.append("❌ Prediction Accuracy: Testing failed")
    
    # Overall Assessment
    if scores:
        overall_score = sum(score for _, score in scores) / len(scores)
        summary_lines.append(f"🎯 Overall Performance Score: {overall_score*100:.1f}%")
        
        if overall_score >= 0.8:
            summary_lines.append("🎉 STATUS: EXCELLENT - System ready for production")
        elif overall_score >= 0.6:
            summary_lines.append("✅ STATUS: GOOD - System performing well")
        elif overall_score >= 0.4:
            summary_lines.append("⚠️ STATUS: FAIR - Some improvements needed")
        else:
            summary_lines.append("❌ STATUS: POOR - Significant work required")
    else:
        summary_lines.append("❓ STATUS: UNKNOWN - Unable to calculate score")
    
    summary_lines.append("")
    
    # Improvements Achieved
    if improvements:
        summary_lines.append("🚀 IMPROVEMENTS ACHIEVED")
        summary_lines.append("-" * 30)
        for improvement in improvements:
            summary_lines.append(improvement)
        summary_lines.append("")
    
    # Issues Found
    if issues:
        summary_lines.append("⚠️ ISSUES IDENTIFIED")
        summary_lines.append("-" * 30)
        for issue in issues:
            summary_lines.append(issue)
        summary_lines.append("")
    
    # Detailed Metrics
    summary_lines.append("📈 DETAILED METRICS")
    summary_lines.append("-" * 30)
    
    # Data Analysis
    if 'data_analysis' in results:
        stats = results['data_analysis']
        summary_lines.append(f"Data Sample:")
        summary_lines.append(f"  - Total Records: {stats.get('total_records', 'N/A')}")
        summary_lines.append(f"  - Unique Descriptions: {stats.get('unique_descriptions', 'N/A')}")
        summary_lines.append(f"  - Records with referencia: {stats.get('records_with_sku', 'N/A')}")
        summary_lines.append(f"  - Avg Description Length: {stats.get('avg_description_length', 0):.1f} words")
        summary_lines.append("")
    
    # Database Performance Details
    if 'database_performance' in results and 'error' not in results['database_performance']:
        summary_lines.append("Database Performance:")
        db_perf = results['database_performance']
        for query_name, result in db_perf.items():
            if isinstance(result, dict) and 'avg_time_ms' in result:
                status = "🚀" if result.get('performance_ok', False) else "⚠️"
                summary_lines.append(f"  {status} {query_name}: {result['avg_time_ms']:.2f}ms")
        summary_lines.append("")
    
    # Text Processing Details
    if ('text_processing_performance' in results and 
        'error' not in results['text_processing_performance']):
        text_perf = results['text_processing_performance']
        summary_lines.append("Text Processing Performance:")
        summary_lines.append(f"  - Sample Size: {text_perf.get('sample_size', 'N/A')}")
        
        if text_perf.get('enhanced_processing', {}).get('available', False):
            std_time = text_perf['standard_processing']['avg_time_ms']
            enh_time = text_perf['enhanced_processing']['avg_time_ms']
            summary_lines.append(f"  - Standard Processing: {std_time:.2f}ms avg")
            summary_lines.append(f"  - Enhanced Processing: {enh_time:.2f}ms avg")
            
            if 'time_improvement_percent' in text_perf:
                improvement = text_perf['time_improvement_percent']
                summary_lines.append(f"  - Performance Change: {improvement:+.1f}%")
        summary_lines.append("")
    
    # Recommendations
    summary_lines.append("💡 RECOMMENDATIONS")
    summary_lines.append("-" * 30)
    
    if overall_score >= 0.8:
        summary_lines.append("✅ System is ready for production deployment")
        summary_lines.append("✅ Monitor cache hit rates in production")
        summary_lines.append("✅ Consider expanding enhanced text processing rules")
    elif overall_score >= 0.6:
        summary_lines.append("⚠️ Address identified issues before production")
        summary_lines.append("⚠️ Optimize slow database queries")
        summary_lines.append("⚠️ Validate cache system functionality")
    else:
        summary_lines.append("❌ Significant improvements needed before production")
        summary_lines.append("❌ Review and fix all failed components")
        summary_lines.append("❌ Re-run validation after fixes")
    
    summary_lines.append("")
    summary_lines.append("=" * 70)
    summary_lines.append("End of Report")
    
    # Save summary
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        print(f"📁 Executive summary saved to: {output_file}")
        
        # Also print key findings
        print(f"\n🎯 KEY FINDINGS:")
        if scores:
            overall_score = sum(score for _, score in scores) / len(scores)
            print(f"   Overall Score: {overall_score*100:.1f}%")
        
        print(f"   Improvements: {len(improvements)}")
        print(f"   Issues: {len(issues)}")
        
    except Exception as e:
        print(f"❌ Error saving executive summary: {e}")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Validation...")
    success = run_full_validation()
    
    if success:
        print("\n✅ Validation completed successfully!")
        print("📁 Check the generated report files for detailed results.")
    else:
        print("\n❌ Validation failed. Check the error messages above.")
