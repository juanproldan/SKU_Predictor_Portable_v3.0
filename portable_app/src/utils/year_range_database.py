#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Year Range Database Optimization Module

This module provides optimized database queries using year range aggregation
for improved automotive parts prediction accuracy and performance.

Key Features:
- Year range-based SKU prediction with improved frequency counting
- Optimized queries that search year ranges instead of individual years
- Backward compatibility with existing prediction system

Author: Augment Agent
Date: 2025-08-02
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
import os


class YearRangeDatabaseOptimizer:
    """
    Optimized database interface using year range aggregation for automotive parts prediction.
    
    This class provides methods to query the new year range tables for improved
    frequency counting and more accurate automotive parts predictions.
    """
    
    def __init__(self, db_path: str):
        """Initialize the year range database optimizer."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._connection = None
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper error handling."""
        if self._connection is None:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database not found: {self.db_path}")
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_sku_predictions_year_range(self, maker: str, model, series: str,
                                     description: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get SKU predictions using year range optimization.

        This method searches the sku_year_ranges table for parts that are compatible
        with the specified year, providing much more accurate frequency counts.

        Args:
            maker: Vehicle manufacturer
            model: Vehicle year (can be string or int)
            series: Vehicle series
            description: Part description (original or normalized)
            limit: Maximum number of results

        Returns:
            List of prediction dictionaries with SKU, frequency, and confidence
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        predictions = []

        # Convert model to integer for year calculations
        try:
            target_year = int(model) if model and str(model).isdigit() else None
        except (ValueError, TypeError):
            target_year = None
        
        # Try exact description match first (highest confidence)
        try:
            cursor.execute("""
                SELECT referencia, frequency, start_year, end_year
                FROM sku_year_ranges
                WHERE LOWER(maker) = LOWER(?) 
                AND LOWER(series) = LOWER(?)
                AND (LOWER(descripcion) = LOWER(?) OR LOWER(normalized_descripcion) = LOWER(?))
                AND ? BETWEEN start_year AND end_year
                ORDER BY frequency DESC
                LIMIT ?
            """, (maker, series, description, description, model, limit))
            
            exact_results = cursor.fetchall()
            
            for row in exact_results:
                referencia, frequency, start_year, end_year = row
                
                # Calculate confidence based on frequency and year range coverage
                confidence = self._calculate_year_range_confidence(frequency, start_year, end_year, target_year, "exact")
                
                predictions.append({
                    'sku': referencia,
                    'frequency': frequency,
                    'confidence': confidence,
                    'source': 'Year-Range-Exact',
                    'year_range': f"{start_year}-{end_year}"
                })
                
                self.logger.debug(f"Year range exact match: {referencia} (freq: {frequency}, range: {start_year}-{end_year})")
        
        except Exception as e:
            self.logger.error(f"Error in exact year range query: {e}")
        
        # If no exact matches, try fuzzy description matching
        if not predictions:
            try:
                cursor.execute("""
                    SELECT referencia, frequency, start_year, end_year
                    FROM sku_year_ranges
                    WHERE LOWER(maker) = LOWER(?) 
                    AND LOWER(series) = LOWER(?)
                    AND (LOWER(descripcion) LIKE LOWER(?) OR LOWER(normalized_descripcion) LIKE LOWER(?))
                    AND ? BETWEEN start_year AND end_year
                    ORDER BY frequency DESC
                    LIMIT ?
                """, (maker, series, f"%{description}%", f"%{description}%", model, limit))
                
                fuzzy_results = cursor.fetchall()
                
                for row in fuzzy_results:
                    referencia, frequency, start_year, end_year = row
                    
                    # Lower confidence for fuzzy matches
                    confidence = self._calculate_year_range_confidence(frequency, start_year, end_year, target_year, "fuzzy")
                    
                    predictions.append({
                        'sku': referencia,
                        'frequency': frequency,
                        'confidence': confidence,
                        'source': 'Year-Range-Fuzzy',
                        'year_range': f"{start_year}-{end_year}"
                    })
                    
                    self.logger.debug(f"Year range fuzzy match: {referencia} (freq: {frequency}, range: {start_year}-{end_year})")
            
            except Exception as e:
                self.logger.error(f"Error in fuzzy year range query: {e}")
        
        return predictions
    

    
    def _calculate_year_range_confidence(self, frequency: int, start_year: int, end_year: int,
                                       target_year, match_type: str) -> float:
        """
        Calculate confidence score based on frequency, year range, and match type.
        
        Args:
            frequency: Total frequency across the year range
            start_year: Start of the year range
            end_year: End of the year range
            target_year: The year being searched for
            match_type: Type of match (exact, fuzzy, vin)
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence from frequency (improved thresholds)
        if frequency >= 20:
            base_confidence = 0.9
        elif frequency >= 10:
            base_confidence = 0.8
        elif frequency >= 5:
            base_confidence = 0.7
        elif frequency >= 3:
            base_confidence = 0.6
        else:
            base_confidence = 0.5
        
        # Adjust based on match type
        match_multipliers = {
            'exact': 1.0,
            'fuzzy': 0.85,
            'vin': 0.9
        }
        
        confidence = base_confidence * match_multipliers.get(match_type, 0.8)
        
        # Bonus for year ranges that include the target year in the middle (more reliable)
        # Only apply if target_year is valid
        if target_year is not None and start_year is not None and end_year is not None:
            try:
                year_range_span = end_year - start_year + 1
                if year_range_span > 1:
                    # Calculate position within range (0.0 = start, 1.0 = end, 0.5 = middle)
                    position_in_range = (target_year - start_year) / (end_year - start_year)

                    # Bonus for being in the middle of the range (more reliable data)
                    if 0.2 <= position_in_range <= 0.8:
                        confidence *= 1.05  # Small bonus for middle positions
            except (TypeError, ZeroDivisionError):
                # If year calculations fail, just use base confidence
                pass
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def get_year_range_statistics(self) -> Dict[str, Any]:
        """Get statistics about the year range optimization."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # SKU year range statistics
            cursor.execute("SELECT COUNT(*) FROM sku_year_ranges")
            stats['sku_year_ranges'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(frequency) FROM sku_year_ranges")
            stats['avg_sku_frequency'] = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(end_year - start_year + 1) FROM sku_year_ranges")
            stats['avg_sku_year_span'] = cursor.fetchone()[0] or 0
            
        except Exception as e:
            self.logger.error(f"Error getting year range statistics: {e}")
        
        return stats
