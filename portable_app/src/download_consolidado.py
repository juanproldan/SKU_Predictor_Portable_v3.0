#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Consolidado.json Downloader

This script downloads the latest Consolidado.json file from the Fixacar S3 bucket
and saves it to the Source_Files directory. Designed to be run as a scheduled task
for automated data updates.

Author: Augment Agent
Date: 2025-07-24
"""

import os
import sys
import requests
import json
import datetime
import logging
from pathlib import Path
import shutil
import tempfile

# Configuration
CONSOLIDADO_URL = "https://fixacar-public-prod.s3.amazonaws.com/reportes/Consolidado.json"
# Use relative path for client deployment - always download to Source_Files relative to executable location
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable - executable is in client folder root
    TARGET_DIR = os.path.join(os.path.dirname(sys.executable), "Source_Files")
else:
    # Running as Python script - for development/testing, use project structure
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up from src/ to project root
    TARGET_DIR = os.path.join(project_root, "Fixacar_SKU_Predictor_CLIENT", "Source_Files")
BACKUP_ENABLED = False
TIMEOUT_SECONDS = 300  # 5 minutes timeout
CHUNK_SIZE = 8192  # 8KB chunks for download

def setup_logging():
    """Setup logging configuration."""
    log_dir = Path(TARGET_DIR).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"consolidado_download_{datetime.datetime.now().strftime('%Y%m%d')}.log"

    # Configure logging with UTF-8 encoding for file handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Configure console handler with proper encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Set formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def backup_existing_file(target_path, logger):
    """Create backup of existing Consolidado.json if it exists."""
    if not os.path.exists(target_path):
        logger.info("No existing Consolidado.json found - no backup needed")
        return True
    
    if not BACKUP_ENABLED:
        logger.info("Backup disabled - overwriting existing file")
        return True
    
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"Consolidado_backup_{timestamp}.json"
        backup_path = os.path.join(os.path.dirname(target_path), backup_name)
        
        shutil.copy2(target_path, backup_path)
        logger.info(f"[OK] Backup created: {backup_name}")
        return True

    except Exception as e:
        logger.error(f"[ERROR] Failed to create backup: {e}")
        return False

def validate_json_file(file_path, logger):
    """Validate that the downloaded file is valid JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic validation - check if it's a list and has some content
        if isinstance(data, list) and len(data) > 0:
            logger.info(f"[OK] JSON validation passed - {len(data)} records found")
            return True
        else:
            logger.error("[ERROR] JSON validation failed - empty or invalid structure")
            return False

    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] JSON validation failed - invalid JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"[ERROR] JSON validation failed - error reading file: {e}")
        return False

def download_consolidado(logger):
    """Download Consolidado.json from S3 and save to target directory."""
    
    # Ensure target directory exists
    os.makedirs(TARGET_DIR, exist_ok=True)
    target_path = os.path.join(TARGET_DIR, "Consolidado.json")
    
    logger.info("[START] Starting Consolidado.json download...")
    logger.info(f"[SOURCE] Source: {CONSOLIDADO_URL}")
    logger.info(f"[TARGET] Target: {target_path}")
    
    # Create backup of existing file
    if not backup_existing_file(target_path, logger):
        logger.warning("⚠️ Backup failed, but continuing with download...")
    
    try:
        # Download to temporary file first
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
            
            logger.info("[DOWNLOAD] Initiating download...")
            response = requests.get(CONSOLIDADO_URL, stream=True, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()

            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                logger.info(f"[SIZE] File size: {total_size / (1024*1024):.1f} MB")
            
            # Download in chunks
            downloaded = 0
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    temp_file.write(chunk)
                    downloaded += len(chunk)
                    
                    # Progress logging every 10MB
                    if downloaded % (10 * 1024 * 1024) == 0:
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"[PROGRESS] Progress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)")
                        else:
                            logger.info(f"[PROGRESS] Downloaded: {downloaded / (1024*1024):.1f} MB")
        
        logger.info(f"[OK] Download completed: {downloaded / (1024*1024):.1f} MB")

        # Validate the downloaded file
        if not validate_json_file(temp_path, logger):
            os.unlink(temp_path)
            return False

        # Move temp file to final location
        shutil.move(temp_path, target_path)
        logger.info(f"[OK] File saved successfully: {target_path}")

        return True

    except requests.exceptions.Timeout:
        logger.error(f"[ERROR] Download timeout after {TIMEOUT_SECONDS} seconds")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"[ERROR] Download failed - Network error: {e}")
        return False
    except Exception as e:
        logger.error(f"[ERROR] Download failed - Unexpected error: {e}")
        return False
    finally:
        # Clean up temp file if it still exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

def main():
    """Main function."""
    print("=" * 60)
    print("FIXACAR CONSOLIDADO.JSON DOWNLOADER")
    print("=" * 60)

    logger = setup_logging()

    try:
        success = download_consolidado(logger)

        if success:
            logger.info("[SUCCESS] Download completed successfully!")
            print("\n[SUCCESS] Consolidado.json updated successfully")
            return 0
        else:
            logger.error("[FAILED] Download failed!")
            print("\n[FAILED] Could not download Consolidado.json")
            return 1

    except KeyboardInterrupt:
        logger.info("[CANCELLED] Download cancelled by user")
        print("\n[CANCELLED] Download cancelled")
        return 1
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {e}")
        print(f"\n[ERROR] Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    # Keep window open if run directly (not from command line)
    if len(sys.argv) == 1:
        input("\nPress Enter to exit...")
    
    sys.exit(exit_code)
