#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart SKU Prediction Cache System
Implements multi-level caching for maker/model/series + Description combinations

Author: Augment Agent
Date: 2025-07-25
"""

import hashlib
import json
import time
import sqlite3
import os
from typing import Dict, List, Tuple, Optional
import pickle
from datetime import datetime

class SKUPredictionCache:
    """
    Multi-level caching system for SKU predictions based on maker/model/series + Description
    
    Level 1: In-memory cache for current session (fastest)
    Level 2: SQLite persistent cache for cross-session storage
    Level 3: Performance statistics and monitoring
    """
    
    def __init__(self, max_memory_cache=1000, cache_db_path=None):
        self.memory_cache = {}  # In-memory cache
        self.max_memory_cache = max_memory_cache
        if cache_db_path is None:
            # Use utils/performance_improvements/cache as default
            cache_db_path = os.path.join(os.path.dirname(__file__), "prediction_cache.db")
        self.cache_db_path = cache_db_path
        self.hit_count = 0
        self.miss_count = 0
        self.session_start = time.time()
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(cache_db_path), exist_ok=True)
        
        # Initialize persistent cache database
        self._init_cache_db()
        
        print(f"🚀 SKU Prediction Cache initialized")
        print(f"   Memory cache limit: {max_memory_cache} entries")
        print(f"   Persistent cache: {cache_db_path}")
    
    def _init_cache_db(self):
        """Initialize SQLite cache database with optimized schema"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_cache (
            cache_key TEXT PRIMARY KEY,
            maker TEXT NOT NULL,
            model TEXT NOT NULL,
            series TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            predictions TEXT NOT NULL,  -- JSON string of predictions
            confidence_scores TEXT NOT NULL,  -- JSON string of confidence scores
            sources TEXT NOT NULL,  -- JSON string of sources
            timestamp REAL NOT NULL,
            hit_count INTEGER DEFAULT 1,
            last_accessed REAL NOT NULL
        )
        ''')
        
        # Create indexes for faster lookups and maintenance
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cache_timestamp ON prediction_cache(timestamp)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cache_last_accessed ON prediction_cache(last_accessed)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cache_make_year_series ON prediction_cache(make, year, series)
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_cache_key(self, make: str, year: str, series: str, descripcion: str) -> str:
        """
        Generate unique cache key for prediction inputs
        Uses maker/model/series + normalized description for optimal hit rate
        """
        # Normalize inputs for consistent caching
        normalized_input = f"{make.lower().strip()}|{year.strip()}|{series.lower().strip()}|{description.lower().strip()}"
        return hashlib.md5(normalized_input.encode()).hexdigest()
    
    def get_cached_prediction(self, maker: str, model: str, series: str, descripcion: str) -> Optional[Dict]:
        """
        Retrieve cached prediction if available
        Returns: Dict with predictions, confidence scores, and sources, or None if not cached
        """
        descripcion_hash = hashlib.md5(descripcion.encode()).hexdigest()[:8]
        cache_key = f'{maker}_{model}_{series}_{descripcion_hash}'
        current_time = time.time()

        # Level 1: Check in-memory cache first (fastest)
        if cache_key in self.memory_cache:
            self.hit_count += 1
            cache_entry = self.memory_cache[cache_key]
            print(f"  🚀 Cache HIT (Memory): {descripcion[:30]}... (used {cache_entry.get('hit_count', 1)} times)")
            return cache_entry['data']
        
        # Level 2: Check persistent cache database
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Cache valid for 24 hours
        cache_expiry = current_time - 86400  # 24 hours ago
        
        cursor.execute('''
        SELECT predictions, confidence_scores, sources, hit_count 
        FROM prediction_cache 
        WHERE cache_key = ? AND timestamp > ?
        ''', (cache_key, cache_expiry))
        
        result = cursor.fetchone()
        
        if result:
            predictions_json, confidence_json, sources_json, hit_count = result
            cached_data = {
                'predictions': json.loads(predictions_json),
                'confidence_scores': json.loads(confidence_json),
                'sources': json.loads(sources_json)
            }
            
            # Update hit count and last accessed time
            cursor.execute('''
            UPDATE prediction_cache 
            SET hit_count = hit_count + 1, last_accessed = ?
            WHERE cache_key = ?
            ''', (current_time, cache_key))
            
            conn.commit()
            conn.close()
            
            # Add to memory cache for faster future access
            self._add_to_memory_cache(cache_key, cached_data, hit_count + 1)
            
            self.hit_count += 1
            print(f"  🚀 Cache HIT (Database): {description[:30]}... (used {hit_count + 1} times)")
            return cached_data
        
        conn.close()
        self.miss_count += 1
        print(f"  ❌ Cache MISS: {descripcion[:30]}...")
        return None

    def cache_prediction(self, maker: str, model: str, series: str, descripcion: str,
                        predictions: List[Dict], confidence_scores: List[float], sources: List[str]):
        """Cache a new prediction result"""
        descripcion_hash = hashlib.md5(descripcion.encode()).hexdigest()[:8]
        cache_key = f'{maker}_{model}_{series}_{descripcion_hash}'
        current_time = time.time()
        
        cached_data = {
            'predictions': predictions,
            'confidence_scores': confidence_scores,
            'sources': sources
        }
        
        # Add to memory cache
        self._add_to_memory_cache(cache_key, cached_data, 1)
        
        # Add to persistent cache
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO prediction_cache 
        (cache_key = f'{maker}_{model}_{series}_{descripcion_hash}', predictions, confidence_scores, sources, timestamp, last_accessed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cache_key = f'{maker}_{model}_{series}_{descripcion_hash}',
            json.dumps(predictions), json.dumps(confidence_scores), json.dumps(sources),
            current_time, current_time
        ))
        
        conn.commit()
        conn.close()
        
        print(f"  💾 Cached prediction: {description[:30]}... (maker: {make}, model: {year}, series: {series})")
    
    def _add_to_memory_cache(self, cache_key: str, data: Dict, hit_count: int):
        """Add item to memory cache with LRU eviction"""
        if len(self.memory_cache) >= self.max_memory_cache:
            # Remove oldest item (simple FIFO, could implement proper LRU)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        self.memory_cache[cache_key] = {
            'data': data,
            'hit_count': hit_count,
            'cached_at': time.time()
        }
    
    def get_cache_stats(self) -> Dict:
        """Get comprehensive cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        session_duration = time.time() - self.session_start
        
        # Get database statistics
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM prediction_cache')
        total_cached_entries = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(hit_count) FROM prediction_cache')
        avg_hit_count = cursor.fetchone()[0] or 0
        
        cursor.execute('''
        SELECT make, year, series, COUNT(*) as count 
        FROM prediction_cache 
        GROUP BY make, year, series 
        ORDER BY count DESC 
        LIMIT 5
        ''')
        top_combinations = cursor.fetchall()
        
        conn.close()
        
        return {
            'session_stats': {
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': total_requests,
                'session_duration_minutes': round(session_duration / 60, 2)
            },
            'cache_stats': {
                'memory_cache_size': len(self.memory_cache),
                'memory_cache_limit': self.max_memory_cache,
                'persistent_cache_entries': total_cached_entries,
                'average_hit_count': round(avg_hit_count, 2)
            },
            'top_combinations': [
                {'make': combo[0], 'year': combo[1], 'series': combo[2], 'requests': combo[3]}
                for combo in top_combinations
            ]
        }
    
    def clear_old_cache(self, days_old: int = 7):
        """Clear cache entries older than specified days"""
        cutoff_time = time.time() - (days_old * 86400)
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM prediction_cache WHERE timestamp < ?', (cutoff_time,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"🧹 Cleared {deleted_count} old cache entries (older than {days_old} days)")
        return deleted_count
    
    def get_cache_efficiency_report(self) -> str:
        """Generate a detailed cache efficiency report"""
        stats = self.get_cache_stats()
        
        report = f"""
🚀 SKU Prediction Cache Efficiency Report
{'='*50}

📊 Session Performance:
   • Cache Hit Rate: {stats['session_stats']['hit_rate_percent']:.1f}%
   • Total Requests: {stats['session_stats']['total_requests']}
   • Cache Hits: {stats['session_stats']['hit_count']}
   • Cache Misses: {stats['session_stats']['miss_count']}
   • Session Duration: {stats['session_stats']['session_duration_minutes']:.1f} minutes

💾 Cache Storage:
   • Memory Cache: {stats['cache_stats']['memory_cache_size']}/{stats['cache_stats']['memory_cache_limit']} entries
   • Persistent Cache: {stats['cache_stats']['persistent_cache_entries']} entries
   • Average Reuse: {stats['cache_stats']['average_hit_count']:.1f} times per entry

🔥 Most Popular Combinations:"""
        
        for i, combo in enumerate(stats['top_combinations'], 1):
            report += f"\n   {i}. {combo['make']} {combo['year']} {combo['series']} - {combo['requests']} requests"
        
        # Performance assessment
        hit_rate = stats['session_stats']['hit_rate_percent']
        if hit_rate >= 30:
            assessment = "🎯 EXCELLENT - High cache efficiency"
        elif hit_rate >= 20:
            assessment = "✅ GOOD - Decent cache performance"
        elif hit_rate >= 10:
            assessment = "⚠️ FAIR - Room for improvement"
        else:
            assessment = "❌ POOR - Cache not effective"
        
        report += f"\n\n📈 Assessment: {assessment}"
        
        return report


# Global cache instance for the application
sku_cache = None

def initialize_cache(max_memory_cache=1000, cache_db_path=None):
    """Initialize the global cache instance"""
    global sku_cache
    sku_cache = SKUPredictionCache(max_memory_cache, cache_db_path)
    return sku_cache

def get_cache():
    """Get the global cache instance"""
    global sku_cache
    if sku_cache is None:
        sku_cache = initialize_cache()
    return sku_cache
