#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Query Optimization Module
Creates optimized indexes and implements query result caching for better performance

Author: Augment Agent
Date: 2025-07-25
"""

import sqlite3
import time
import json
import os
from typing import Dict, List, Tuple, Optional
import hashlib

class DatabaseOptimizer:
    """
    Database optimization strategies for better query performance
    Focuses on real query patterns used in SKU prediction
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.query_cache = {}  # In-memory query result cache
        self.query_stats = {}  # Query performance statistics
        
    def create_optimized_indexes(self):
        """Create optimized indexes for common query patterns"""
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"🔧 Creating optimized indexes for: {self.db_path}")
        
        # Indexes for SKU prediction queries based on actual usage patterns
        optimization_queries = [
            # 1. Composite index for exact maker/model/series/Description matching (Maestro-style queries)
            '''CREATE INDEX IF NOT EXISTS idx_exact_match
               ON processed_consolidado(maker, model, series, descripcion)''',
            
            # 2. Index for SKU frequency analysis (Database source queries)
            '''CREATE INDEX IF NOT EXISTS idx_referencia_frequency
               ON processed_consolidado(referencia, maker, model)''',

            # 3. Index for description-based fuzzy matching
            '''CREATE INDEX IF NOT EXISTS idx_description_search
               ON processed_consolidado(descripcion, referencia)''',
            
            # 4. Index for VIN-based queries (VIN prediction)
            '''CREATE INDEX IF NOT EXISTS idx_vin_lookup 
               ON processed_consolidado(vin_number)''',
            
            # 5. Index for Make/Year combinations (common filtering)
            '''CREATE INDEX IF NOT EXISTS idx_make_year 
               ON processed_consolidado(maker, model)''',
            
            # 6. Index for SKU-only queries (SKU validation)
            '''CREATE INDEX IF NOT EXISTS idx_referencia_only
               ON processed_consolidado(referencia)''',

            # 7. Covering index for common SELECT patterns
            '''CREATE INDEX IF NOT EXISTS idx_covering_referencia_search
               ON processed_consolidado(maker, model, series, referencia, descripcion)'''
        ]
        
        created_count = 0
        for query in optimization_queries:
            try:
                start_time = time.time()
                cursor.execute(query)
                end_time = time.time()
                
                index_name = query.split('idx_')[1].split(' ')[0]
                print(f"  ✅ Created index: {index_name} ({(end_time - start_time)*1000:.1f}ms)")
                created_count += 1
                
            except Exception as e:
                index_name = query.split('idx_')[1].split(' ')[0] if 'idx_' in query else 'unknown'
                print(f"  ❌ Failed to create index {index_name}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"🎯 Created {created_count}/{len(optimization_queries)} indexes successfully")
        return created_count == len(optimization_queries)
    
    def analyze_query_performance(self):
        """Analyze database query performance and suggest optimizations"""
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"📊 Analyzing query performance for: {self.db_path}")
        
        # Test common query patterns used in SKU prediction
        test_queries = [
            # Query 1: Basic count (baseline)
            ("Basic Count", "SELECT COUNT(*) FROM processed_consolidado"),
            
            # Query 2: Make-based filtering (common in Maestro search)
            ("Make Filter", "SELECT COUNT(*) FROM processed_consolidado WHERE maker = 'Toyota'"),
            
            # Query 3: Make + Year filtering (common combination)
            ("Make+Year Filter", "SELECT COUNT(*) FROM processed_consolidado WHERE maker = 'Toyota' AND model = 2020"),
            
            # Query 4: SKU frequency analysis (Database source)
            ("SKU Frequency", "SELECT referencia, COUNT(*) FROM processed_consolidado WHERE referencia IS NOT NULL GROUP BY referencia ORDER BY COUNT(*) DESC LIMIT 10"),
            
            # Query 5: Description search (fuzzy matching)
            ("Description Search", "SELECT COUNT(*) FROM processed_consolidado WHERE descripcion LIKE '%parachoques%'"),
            
            # Query 6: Complex join-like query (full prediction pattern)
            ("Full Prediction Pattern",
             "SELECT referencia, COUNT(*) FROM processed_consolidado WHERE maker = 'Toyota' AND model = 2020 AND descripcion LIKE '%delantero%' GROUP BY referencia")
        ]
        
        performance_results = {}
        
        for query_name, query in test_queries:
            try:
                # Warm up
                cursor.execute(query)
                cursor.fetchall()
                
                # Actual timing
                start_time = time.time()
                cursor.execute(query)
                results = cursor.fetchall()
                end_time = time.time()
                
                query_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                performance_results[query_name] = {
                    'time_ms': round(query_time, 2),
                    'result_count': len(results),
                    'status': 'fast' if query_time < 50 else 'slow' if query_time > 200 else 'medium'
                }
                
                status_emoji = "🚀" if query_time < 50 else "⚠️" if query_time > 200 else "✅"
                print(f"  {status_emoji} {query_name}: {query_time:.2f}ms ({len(results)} rows)")
                
            except Exception as e:
                performance_results[query_name] = {
                    'time_ms': -1,
                    'result_count': 0,
                    'status': 'error',
                    'error': str(e)
                }
                print(f"  ❌ {query_name}: ERROR - {e}")
        
        conn.close()
        
        # Performance summary
        fast_queries = sum(1 for r in performance_results.values() if r['status'] == 'fast')
        total_queries = len([r for r in performance_results.values() if r['status'] != 'error'])
        
        print(f"\n📈 Performance Summary: {fast_queries}/{total_queries} queries are fast (<50ms)")
        
        return performance_results
    
    def get_database_stats(self):
        """Get comprehensive database statistics"""
        if not os.path.exists(self.db_path):
            return {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # Basic table info
            cursor.execute("SELECT COUNT(*) FROM processed_consolidado")
            stats['total_records'] = cursor.fetchone()[0]
            
            # Records with SKUs
            cursor.execute("SELECT COUNT(*) FROM processed_consolidado WHERE referencia IS NOT NULL AND referencia != ''")
            stats['records_with_sku'] = cursor.fetchone()[0]

            # Unique SKUs
            cursor.execute("SELECT COUNT(DISTINCT referencia) FROM processed_consolidado WHERE referencia IS NOT NULL AND referencia != ''")
            stats['unique_skus'] = cursor.fetchone()[0]
            
            # Unique makes
            cursor.execute("SELECT COUNT(DISTINCT maker) FROM processed_consolidado WHERE maker IS NOT NULL")
            stats['unique_makes'] = cursor.fetchone()[0]
            
            # Year range
            cursor.execute("SELECT MIN(model), MAX(model) FROM processed_consolidado WHERE model IS NOT NULL")
            year_range = cursor.fetchone()
            stats['year_range'] = f"{year_range[0]}-{year_range[1]}" if year_range[0] else "N/A"
            
            # Top makes
            cursor.execute("""
            SELECT maker, COUNT(*) as count 
            FROM processed_consolidado 
            WHERE maker IS NOT NULL 
            GROUP BY maker 
            ORDER BY count DESC 
            LIMIT 5
            """)
            stats['top_makes'] = [{'make': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Database file size
            stats['file_size_mb'] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            
        except Exception as e:
            stats['error'] = str(e)
        
        conn.close()
        return stats


class QueryResultCache:
    """
    In-memory cache for database query results
    Speeds up repeated queries during prediction pipeline
    """
    
    def __init__(self, max_cache_size=500):
        self.cache = {}
        self.max_cache_size = max_cache_size
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_query_key(self, query: str, params: tuple = ()) -> str:
        """Generate cache key for query + parameters"""
        query_string = f"{query}|{str(params)}"
        return hashlib.md5(query_string.encode()).hexdigest()
    
    def get_cached_result(self, query: str, params: tuple = ()) -> Optional[List]:
        """Get cached query result if available"""
        cache_key = self._generate_query_key(query, params)
        
        if cache_key in self.cache:
            self.hit_count += 1
            return self.cache[cache_key]['result']
        
        self.miss_count += 1
        return None
    
    def cache_result(self, query: str, params: tuple, result: List):
        """Cache query result"""
        cache_key = self._generate_query_key(query, params)
        
        # Implement simple LRU eviction
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def execute_cached_query(self, conn: sqlite3.Connection, query: str, params: tuple = ()) -> List:
        """Execute query with caching"""
        # Check cache first
        cached_result = self.get_cached_result(query, params)
        if cached_result is not None:
            return cached_result
        
        # Execute query
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        
        # Cache result
        self.cache_result(query, params, result)
        
        return result
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': len(self.cache),
            'cache_limit': self.max_cache_size
        }
    
    def clear_cache(self):
        """Clear all cached results"""
        self.cache.clear()
        print(f"🧹 Query cache cleared")


# Global instances
db_optimizer = None
query_cache = None

def initialize_database_optimization(db_path: str):
    """Initialize database optimization for the given database"""
    global db_optimizer, query_cache
    
    db_optimizer = DatabaseOptimizer(db_path)
    query_cache = QueryResultCache()
    
    print(f"🔧 Database optimization initialized for: {db_path}")
    return db_optimizer, query_cache

def get_optimizer():
    """Get the global database optimizer instance"""
    return db_optimizer

def get_query_cache():
    """Get the global query cache instance"""
    return query_cache
