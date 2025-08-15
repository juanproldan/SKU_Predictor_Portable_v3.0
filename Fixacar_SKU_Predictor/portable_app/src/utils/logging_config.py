#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unified Logging Configuration for SKU Predictor v2.0

This module provides performance-optimized logging configuration across all components.
Reduces verbose logging while maintaining essential information for monitoring and debugging.

Author: Augment Agent
Date: 2025-01-31
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Performance-focused logging levels
class LogLevel:
    """Standardized logging levels for the project"""
    SILENT = logging.CRITICAL + 1  # Only critical errors
    MINIMAL = logging.ERROR        # Errors and critical info
    NORMAL = logging.WARNING       # Default production level
    VERBOSE = logging.INFO         # Detailed information
    DEBUG = logging.DEBUG          # Full debugging

# Default logging configuration
DEFAULT_CONFIG = {
    'level': LogLevel.NORMAL,
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'date_format': '%H:%M:%S',  # Shorter timestamp for performance
    'file_encoding': 'utf-8',
    'console_output': True,
    'file_output': True,
    'progress_indicators': True,
    'batch_logging': True,
    'batch_size': 1000,  # Log summary every N records
}

class PerformanceLogger:
    """
    Performance-optimized logger that reduces I/O overhead and provides
    batch logging capabilities for high-frequency operations.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.logger = self._setup_logger()
        self.batch_counter = 0
        self.batch_messages = []
        
    def _setup_logger(self) -> logging.Logger:
        """Setup the logger with performance-optimized configuration"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.config['level'])
        
        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            self.config['format'],
            datefmt=self.config['date_format']
        )
        
        # Console handler (if enabled)
        if self.config['console_output']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.config['level'])
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if self.config['file_output']:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding=self.config['file_encoding'])
            file_handler.setLevel(self.config['level'])
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def info(self, message: str, batch: bool = False):
        """Log info message with optional batching"""
        if batch and self.config['batch_logging']:
            self._add_to_batch(message, logging.INFO)
        else:
            self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message (always immediate)"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message (always immediate)"""
        self.logger.error(message)
    
    def debug(self, message: str, batch: bool = False):
        """Log debug message with optional batching"""
        if self.config['level'] <= logging.DEBUG:
            if batch and self.config['batch_logging']:
                self._add_to_batch(message, logging.DEBUG)
            else:
                self.logger.debug(message)
    
    def _add_to_batch(self, message: str, level: int):
        """Add message to batch for later processing"""
        self.batch_messages.append((message, level))
        self.batch_counter += 1
        
        if self.batch_counter >= self.config['batch_size']:
            self._flush_batch()
    
    def _flush_batch(self):
        """Flush batched messages"""
        if self.batch_messages:
            # Log a summary instead of individual messages
            summary = f"Processed {len(self.batch_messages)} operations"
            self.logger.info(summary)
            
            # Clear batch
            self.batch_messages.clear()
            self.batch_counter = 0
    
    def progress(self, current: int, total: int, operation: str = "Processing"):
        """Log progress indicator"""
        if self.config['progress_indicators'] and current % self.config['batch_size'] == 0:
            percentage = (current / total) * 100 if total > 0 else 0
            self.logger.info(f"{operation}: {current:,}/{total:,} ({percentage:.1f}%)")

    def create_progress_bar(self, total: int, description: str = "Processing"):
        """Create a progress bar using tqdm if available"""
        try:
            from tqdm import tqdm
            return tqdm(total=total, desc=description, unit="rec",
                       bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]')
        except ImportError:
            # Fallback to None if tqdm not available
            return None
    
    def summary(self, stats: Dict[str, Any]):
        """Log operation summary"""
        summary_lines = [f"Operation Summary:"]
        for key, value in stats.items():
            summary_lines.append(f"  {key}: {value}")
        self.logger.info("\n".join(summary_lines))
    
    def finalize(self):
        """Finalize logging (flush any remaining batches)"""
        self._flush_batch()

# Global logger instances
_loggers: Dict[str, PerformanceLogger] = {}

def get_logger(name: str, config: Optional[Dict[str, Any]] = None) -> PerformanceLogger:
    """Get or create a performance logger instance"""
    if name not in _loggers:
        _loggers[name] = PerformanceLogger(name, config)
    return _loggers[name]

def set_global_log_level(level: int):
    """Set logging level for all existing loggers"""
    for logger in _loggers.values():
        logger.config['level'] = level
        logger.logger.setLevel(level)
        for handler in logger.logger.handlers:
            handler.setLevel(level)

def create_processing_config(verbose: bool = False) -> Dict[str, Any]:
    """Create configuration for data processing operations"""
    return {
        'level': LogLevel.VERBOSE if verbose else LogLevel.NORMAL,
        'batch_logging': True,
        'batch_size': 5000,  # Larger batches for processing
        'progress_indicators': True,
        'console_output': True,
        'file_output': True,
    }

def create_training_config(verbose: bool = False) -> Dict[str, Any]:
    """Create configuration for training operations"""
    return {
        'level': LogLevel.VERBOSE if verbose else LogLevel.NORMAL,
        'batch_logging': False,  # Training needs immediate feedback
        'progress_indicators': True,
        'console_output': True,
        'file_output': True,
    }

def create_application_config(verbose: bool = False) -> Dict[str, Any]:
    """Create configuration for main application"""
    return {
        'level': LogLevel.VERBOSE if verbose else LogLevel.NORMAL,
        'batch_logging': True,
        'batch_size': 100,  # Smaller batches for interactive use
        'progress_indicators': False,  # No progress bars in GUI
        'console_output': True,
        'file_output': False,  # No file logging for GUI
    }

# Convenience functions for common logging patterns
def log_operation_start(logger: PerformanceLogger, operation: str, details: str = ""):
    """Log the start of a major operation"""
    message = f"🚀 Starting {operation}"
    if details:
        message += f": {details}"
    logger.info(message)

def log_operation_complete(logger: PerformanceLogger, operation: str, duration: float, stats: Dict[str, Any] = None):
    """Log the completion of a major operation"""
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        time_str = f"{int(hours)}h {int(minutes)}m {seconds:.1f}s"
    elif minutes > 0:
        time_str = f"{int(minutes)}m {seconds:.1f}s"
    else:
        time_str = f"{seconds:.1f}s"
    
    message = f"✅ Completed {operation} in {time_str}"
    logger.info(message)

    if stats:
        # Check if logger has summary method (PerformanceLogger vs basic logger)
        if hasattr(logger, 'summary'):
            logger.summary(stats)
        else:
            # Fallback for basic logger - log stats manually
            stats_lines = ["Operation Summary:"]
            for key, value in stats.items():
                stats_lines.append(f"  {key}: {value}")
            logger.info("\n".join(stats_lines))

def log_error_with_context(logger: PerformanceLogger, operation: str, error: Exception, context: str = ""):
    """Log an error with context information"""
    message = f"❌ Error in {operation}: {str(error)}"
    if context:
        message += f" (Context: {context})"
    logger.error(message)
