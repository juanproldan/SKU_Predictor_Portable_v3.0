#!/usr/bin/env python3
"""
Optimized database operations for faster SKU prediction
"""

import sqlite3
import time
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
import hashlib

class OptimizedDatabase:
    """Optimized database operations with caching and indexing"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection_pool = []
        self._query_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Initialize optimizations
        self._create_optimized_indexes()
        self._analyze_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with optimizations"""
        conn = sqlite3.connect(self.db_path)
        
        # Enable optimizations
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL") 
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB
        
        return conn
    
    def _create_optimized_indexes(self):
        """Create optimized indexes for common queries"""
        print("🗄️ Creating optimized database indexes...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Indexes for common query patterns
        indexes = [
            # SKU prediction indexes
            "CREATE INDEX IF NOT EXISTS idx_vehicle_sku ON processed_consolidado(maker, model, series, referencia)",
            "CREATE INDEX IF NOT EXISTS idx_description_search ON processed_consolidado(descripcion)",
            "CREATE INDEX IF NOT EXISTS idx_sku_frequency ON processed_consolidado(referencia)",

            # Composite indexes for complex queries
            "CREATE INDEX IF NOT EXISTS idx_vehicle_desc ON processed_consolidado(maker, model, series, descripcion)",
            "CREATE INDEX IF NOT EXISTS idx_maker_desc ON processed_consolidado(maker, descripcion)",

            # Full-text search index (if supported)
            "CREATE VIRTUAL TABLE IF NOT EXISTS fts_descriptions USING fts5(referencia, descripcion, content='processed_consolidado', content_rowid='rowid')",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"  ✅ Created index: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'FTS'}")
            except sqlite3.Error as e:
                if "already exists" not in str(e):
                    print(f"  ⚠️ Index creation warning: {e}")
        
        # Populate FTS index if it was created
        try:
            cursor.execute("INSERT OR REPLACE INTO fts_descriptions SELECT referencia, descripcion FROM processed_consolidado")
            print("  ✅ Populated FTS index")
        except sqlite3.Error:
            pass  # FTS might not be available
        
        conn.commit()
        conn.close()
        print("✅ Database indexes optimized")
    
    def _analyze_database(self):
        """Analyze database for query optimization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("ANALYZE")
            print("✅ Database statistics updated")
        except sqlite3.Error as e:
            print(f"⚠️ Database analysis warning: {e}")
        
        conn.close()
    
    def _get_cache_key(self, query: str, params: tuple) -> str:
        """Generate cache key for query"""
        query_hash = hashlib.md5(f"{query}{params}".encode()).hexdigest()
        return query_hash
    
    def _execute_cached_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute query with caching"""
        cache_key = self._get_cache_key(query, params)
        
        # Check cache first
        if cache_key in self._query_cache:
            self._cache_hits += 1
            return self._query_cache[cache_key]
        
        # Execute query
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Cache results (limit cache size)
        if len(self._query_cache) < 1000:  # Limit cache size
            self._query_cache[cache_key] = results
        
        self._cache_misses += 1
        return results
    
    def get_maestro_predictions_optimized(self, maker: str, model: str, series: str, description: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Optimized Maestro SKU prediction"""
        # Try exact match first (fastest)
        exact_query = """
            SELECT referencia, COUNT(*) as frequency
            FROM processed_consolidado
            WHERE maker = ? AND model = ? AND series = ?
            AND descripcion = ?
            GROUP BY referencia
            ORDER BY frequency DESC
            LIMIT ?
        """
        
        results = self._execute_cached_query(exact_query, (maker, model, series, description.lower(), limit))
        
        if results:
            return [{'sku': row[0], 'frequency': row[1], 'confidence': 0.9} for row in results]
        
        # Fallback to fuzzy match
        fuzzy_query = """
            SELECT referencia, COUNT(*) as frequency
            FROM processed_consolidado
            WHERE maker = ? AND model = ? AND series = ?
            AND descripcion LIKE ?
            GROUP BY referencia
            ORDER BY frequency DESC
            LIMIT ?
        """
        
        like_pattern = f"%{description.lower()}%"
        results = self._execute_cached_query(fuzzy_query, (maker, model, series, like_pattern, limit))
        
        return [{'sku': row[0], 'frequency': row[1], 'confidence': 0.7} for row in results]
    
    def get_database_predictions_optimized(self, description: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Optimized database SKU prediction with frequency-based confidence"""
        
        # Try FTS search first (if available)
        try:
            fts_query = """
                SELECT referencia, COUNT(*) as frequency
                FROM fts_descriptions 
                WHERE fts_descriptions MATCH ?
                GROUP BY referencia 
                HAVING frequency >= 3
                ORDER BY frequency DESC 
                LIMIT ?
            """
            
            results = self._execute_cached_query(fts_query, (description.lower(), limit))
            
            if results:
                predictions = []
                for row in results:
                    frequency = row[1]
                    # Frequency-based confidence (reduced threshold from 20 to 10)
                    if frequency >= 10:
                        confidence = 0.8
                    elif frequency >= 5:
                        confidence = 0.6
                    elif frequency >= 3:
                        confidence = 0.5
                    else:
                        confidence = 0.4
                    
                    predictions.append({
                        'sku': row[0], 
                        'frequency': frequency, 
                        'confidence': confidence
                    })
                
                return predictions
        
        except sqlite3.Error:
            pass  # FTS not available, fallback to LIKE
        
        # Fallback to optimized LIKE search
        like_query = """
            SELECT referencia, COUNT(*) as frequency
            FROM processed_consolidado
            WHERE descripcion LIKE ?
            GROUP BY referencia
            HAVING frequency >= 3
            ORDER BY frequency DESC
            LIMIT ?
        """
        
        like_pattern = f"%{description.lower()}%"
        results = self._execute_cached_query(like_query, (like_pattern, limit))
        
        predictions = []
        for row in results:
            frequency = row[1]
            # Frequency-based confidence (reduced threshold from 20 to 10)
            if frequency >= 10:
                confidence = 0.8
            elif frequency >= 5:
                confidence = 0.6
            elif frequency >= 3:
                confidence = 0.5
            else:
                confidence = 0.4
            
            predictions.append({
                'sku': row[0], 
                'frequency': frequency, 
                'confidence': confidence
            })
        
        return predictions
    
    def get_sku_frequency_optimized(self, sku: str) -> int:
        """Get SKU frequency with caching"""
        query = "SELECT COUNT(*) FROM processed_consolidado WHERE referencia = ?"
        results = self._execute_cached_query(query, (sku,))
        return results[0][0] if results else 0
    
    def batch_sku_frequency(self, skus: List[str]) -> Dict[str, int]:
        """Get frequencies for multiple SKUs in one query"""
        if not skus:
            return {}
        
        placeholders = ','.join(['?' for _ in skus])
        query = f"""
            SELECT referencia, COUNT(*) as frequency
            FROM processed_consolidado 
            WHERE referencia IN ({placeholders})
            GROUP BY referencia
        """
        
        results = self._execute_cached_query(query, tuple(skus))
        return {row[0]: row[1] for row in results}
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache performance statistics"""
        total_queries = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_queries * 100) if total_queries > 0 else 0
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate_percent': hit_rate,
            'cached_queries': len(self._query_cache)
        }
    
    def clear_cache(self):
        """Clear query cache"""
        self._query_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def optimize_for_production(self):
        """Apply production optimizations"""
        print("🚀 Applying production database optimizations...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Production optimizations
        optimizations = [
            "PRAGMA optimize",
            "VACUUM",
            "REINDEX"
        ]
        
        for opt in optimizations:
            try:
                cursor.execute(opt)
                print(f"  ✅ Applied: {opt}")
            except sqlite3.Error as e:
                print(f"  ⚠️ Optimization warning: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Production optimizations applied")

# Global database instance
_optimized_db = None

def get_optimized_database(db_path: str = "Source_Files/processed_consolidado.db") -> OptimizedDatabase:
    """Get global optimized database instance"""
    global _optimized_db
    if _optimized_db is None:
        _optimized_db = OptimizedDatabase(db_path)
    return _optimized_db

def benchmark_database_performance(db_path: str = "Source_Files/processed_consolidado.db"):
    """Benchmark database performance improvements"""
    print("📊 Benchmarking database performance...")
    
    db = get_optimized_database(db_path)
    
    # Test queries
    test_cases = [
        ("Toyota", "2020", "Corolla", "capo"),
        ("Honda", "2019", "Civic", "farola derecha"),
        ("Mazda", "2021", "CX-5", "paragolpes delantero")
    ]
    
    total_time = 0
    for maker, model, series, desc in test_cases:
        start_time = time.time()
        
        # Test Maestro predictions
        maestro_results = db.get_maestro_predictions_optimized(maker, model, series, desc)
        
        # Test database predictions
        db_results = db.get_database_predictions_optimized(desc)
        
        end_time = time.time()
        query_time = (end_time - start_time) * 1000
        total_time += query_time
        
        print(f"  Query: {maker} {model} {series} '{desc}' - {query_time:.1f}ms")
        print(f"    Maestro: {len(maestro_results)} results")
        print(f"    Database: {len(db_results)} results")
    
    avg_time = total_time / len(test_cases)
    print(f"  📊 Average query time: {avg_time:.1f}ms")
    
    # Show cache stats
    cache_stats = db.get_cache_stats()
    print(f"  📊 Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%")
    
    return avg_time
