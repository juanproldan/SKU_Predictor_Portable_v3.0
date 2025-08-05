"""
Data access layer for SKU Predictor v2.0

This module provides a centralized interface for all data operations,
including database access, file operations, and data validation.
"""

import sqlite3
import pandas as pd
import os
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
import time

try:
    from config.settings import get_config
    from core.error_handler import get_error_handler, ErrorCategory, ErrorSeverity
except ImportError:
    # Fallback for development
    def get_config():
        class MockConfig:
            database = type('obj', (object,), {
                'connection_timeout': 30,
                'max_retries': 3,
                'retry_delay': 1.0,
                'default_limit': 1000,
                'batch_size': 100
            })
            paths = type('obj', (object,), {
                'database_file': 'data/fixacar_history.db',
                'maestro_file': 'data/Maestro.xlsx',
                'equivalencias_file': 'Source_Files/Equivalencias.xlsx'
            })
        return MockConfig()

    def get_error_handler():
        class MockErrorHandler:
            def handle_error(self, *args, **kwargs):
                print(f"Error: {args}")
        return MockErrorHandler()


@dataclass
class MaestroEntry:
    """Data class for Maestro entries."""
    maestro_id: Optional[int] = None
    vin_make: str = ""
    vin_model: str = ""
    vin_year_min: Optional[int] = None
    vin_year_max: Optional[int] = None
    vin_series_trim: str = ""
    vin_bodystyle: str = ""
    original_description_input: str = ""
    normalized_description_input: str = ""
    equivalencia_row_id: Optional[int] = None
    confirmed_sku: str = ""
    confidence: float = 1.0
    source: str = "UserConfirmed"
    date_added: Optional[str] = None


@dataclass
class HistoricalPart:
    """Data class for historical parts data."""
    id: Optional[int] = None
    vin_number: str = ""
    normalized_description: str = ""
    sku: str = ""
    date_added: Optional[str] = None


class DatabaseManager:
    """Manages database connections and operations with retry logic."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.config = get_config()
        self.error_handler = get_error_handler()

    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup and retry logic."""
        connection = None
        retries = 0

        try:
            while retries < self.config.database.max_retries:
                try:
                    connection = sqlite3.connect(
                        self.db_path,
                        timeout=self.config.database.connection_timeout
                    )
                    connection.row_factory = sqlite3.Row  # Enable column access by name
                    yield connection
                    break

                except sqlite3.Error as e:
                    retries += 1
                    if connection:
                        connection.close()
                        connection = None

                    if retries >= self.config.database.max_retries:
                        self.error_handler.handle_error(
                            e,
                            f"connecting to database after {retries} retries",
                            ErrorCategory.DATA_ACCESS,
                            ErrorSeverity.HIGH
                        )
                        raise

                    time.sleep(self.config.database.retry_delay)
        finally:
            if connection:
                connection.close()

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_all: bool = True
    ) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())

                if fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.fetchone()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                f"executing query: {query[:100]}...",
                ErrorCategory.DATA_ACCESS,
                ErrorSeverity.MEDIUM
            )
            return []

    def execute_update(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount

        except Exception as e:
            self.error_handler.handle_error(
                e,
                f"executing update: {query[:100]}...",
                ErrorCategory.DATA_ACCESS,
                ErrorSeverity.MEDIUM
            )
            return 0

    def execute_batch(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """Execute a batch of queries for better performance."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount

        except Exception as e:
            self.error_handler.handle_error(
                e,
                f"executing batch query: {query[:100]}...",
                ErrorCategory.DATA_ACCESS,
                ErrorSeverity.MEDIUM
            )
            return 0


class DataRepository:
    """Main data repository providing high-level data access methods."""

    def __init__(self):
        self.config = get_config()
        self.error_handler = get_error_handler()
        self.db_manager = DatabaseManager(self.config.paths.database_file)

    # Historical Parts Operations
    def get_historical_parts(
        self,
        limit: Optional[int] = None,
        vin_filter: Optional[str] = None,
        sku_filter: Optional[str] = None
    ) -> List[HistoricalPart]:
        """Get historical parts data with optional filtering."""
        query = "SELECT * FROM historical_parts WHERE 1=1"
        params = []

        if vin_filter:
            query += " AND vin_number LIKE ?"
            params.append(f"%{vin_filter}%")

        if sku_filter:
            query += " AND sku LIKE ?"
            params.append(f"%{sku_filter}%")

        if limit:
            query += " LIMIT ?"
            params.append(limit)
        else:
            query += f" LIMIT {self.config.database.default_limit}"

        rows = self.db_manager.execute_query(query, tuple(params))

        return [
            HistoricalPart(
                id=row['id'] if 'id' in row.keys() else None,
                vin_number=row['vin_number'] or "",
                normalized_description=row['normalized_description'] or "",
                sku=row['sku'] or "",
                date_added=row['date_added'] if 'date_added' in row.keys() else None
            )
            for row in rows
        ]

    def search_historical_parts_by_description(
        self,
        description: str,
        limit: Optional[int] = None
    ) -> List[HistoricalPart]:
        """Search historical parts by description."""
        query = """
        SELECT * FROM historical_parts
        WHERE normalized_description LIKE ?
        ORDER BY sku
        """

        if limit:
            query += " LIMIT ?"
            params = (f"%{description}%", limit)
        else:
            query += f" LIMIT {self.config.database.default_limit}"
            params = (f"%{description}%",)

        rows = self.db_manager.execute_query(query, params)

        return [
            HistoricalPart(
                id=row['id'] if 'id' in row.keys() else None,
                vin_number=row['vin_number'] or "",
                normalized_description=row['normalized_description'] or "",
                sku=row['sku'] or "",
                date_added=row['date_added'] if 'date_added' in row.keys() else None
            )
            for row in rows
        ]

    # Maestro Operations
    def load_maestro_data(self) -> List[MaestroEntry]:
        """Load Maestro data from Excel file."""
        try:
            if not os.path.exists(self.config.paths.maestro_file):
                return []

            df = pd.read_excel(self.config.paths.maestro_file)

            maestro_entries = []
            for _, row in df.iterrows():
                entry = MaestroEntry(
                    maestro_id=row.get('Maestro_ID'),
                    vin_make=row.get('VIN_Make', ''),
                    vin_model=row.get('VIN_Model', ''),
                    vin_year_min=row.get('VIN_Year_Min'),
                    vin_year_max=row.get('VIN_Year_Max'),
                    vin_series_trim=row.get('VIN_Series_Trim', ''),
                    vin_bodystyle=row.get('VIN_BodyStyle', ''),
                    original_description_input=row.get('Original_Description_Input', ''),
                    normalized_description_input=row.get('Normalized_Description_Input', ''),
                    equivalencia_row_id=row.get('Equivalencia_Row_ID'),
                    confirmed_sku=row.get('Confirmed_SKU', ''),
                    confidence=row.get('Confidence', 1.0),
                    source=row.get('Source', 'UserConfirmed'),
                    date_added=row.get('Date_Added')
                )
                maestro_entries.append(entry)

            return maestro_entries

        except Exception as e:
            self.error_handler.handle_file_error(
                self.config.paths.maestro_file,
                "loading",
                e
            )
            return []

    def save_maestro_entry(self, entry: MaestroEntry) -> bool:
        """Save a new Maestro entry to the Excel file."""
        try:
            # Load existing data
            maestro_entries = self.load_maestro_data()

            # Add new entry
            maestro_entries.append(entry)

            # Convert to DataFrame
            data = []
            for e in maestro_entries:
                data.append({
                    'Maestro_ID': e.maestro_id,
                    'VIN_Make': e.vin_make,
                    'VIN_Model': e.vin_model,
                    'VIN_Year_Min': e.vin_year_min,
                    'VIN_Year_Max': e.vin_year_max,
                    'VIN_Series_Trim': e.vin_series_trim,
                    'VIN_BodyStyle': e.vin_bodystyle,
                    'Original_Description_Input': e.original_description_input,
                    'Normalized_Description_Input': e.normalized_description_input,
                    'Equivalencia_Row_ID': e.equivalencia_row_id,
                    'Confirmed_SKU': e.confirmed_sku,
                    'Confidence': e.confidence,
                    'Source': e.source,
                    'Date_Added': e.date_added
                })

            df = pd.DataFrame(data)
            df.to_excel(self.config.paths.maestro_file, index=False)

            return True

        except Exception as e:
            self.error_handler.handle_file_error(
                self.config.paths.maestro_file,
                "saving",
                e
            )
            return False

    # Equivalencias Operations
    def load_equivalencias_data(self) -> Dict[str, int]:
        """Load equivalencias mapping from Excel file."""
        try:
            if not os.path.exists(self.config.paths.equivalencias_file):
                return {}

            df = pd.read_excel(self.config.paths.equivalencias_file, sheet_name=0)
            equivalencias_map = {}

            for index, row in df.iterrows():
                equivalencia_row_id = index + 1
                for col_name in df.columns:
                    term = row[col_name]
                    if pd.notna(term) and str(term).strip():
                        # Import normalize_text function
                        try:
                            from utils.text_utils import normalize_text
                            normalized_term = normalize_text(str(term))
                        except ImportError:
                            normalized_term = str(term).lower().strip()

                        if normalized_term:
                            equivalencias_map[normalized_term] = equivalencia_row_id

            return equivalencias_map

        except Exception as e:
            self.error_handler.handle_file_error(
                self.config.paths.equivalencias_file,
                "loading",
                e
            )
            return {}

    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database."""
        try:
            stats = {}

            # Count historical parts
            result = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM historical_parts",
                fetch_all=False
            )
            stats['historical_parts_count'] = result['count'] if result else 0

            # Count unique SKUs
            result = self.db_manager.execute_query(
                "SELECT COUNT(DISTINCT sku) as count FROM historical_parts WHERE sku IS NOT NULL",
                fetch_all=False
            )
            stats['unique_skus'] = result['count'] if result else 0

            # Count unique VINs
            result = self.db_manager.execute_query(
                "SELECT COUNT(DISTINCT vin_number) as count FROM historical_parts WHERE vin_number IS NOT NULL",
                fetch_all=False
            )
            stats['unique_vins'] = result['count'] if result else 0

            return stats

        except Exception as e:
            self.error_handler.handle_error(
                e,
                "getting database statistics",
                ErrorCategory.DATA_ACCESS,
                ErrorSeverity.LOW
            )
            return {}


# Global repository instance
_repository = None


def get_repository() -> DataRepository:
    """Get the global data repository instance."""
    global _repository
    if _repository is None:
        _repository = DataRepository()
    return _repository
