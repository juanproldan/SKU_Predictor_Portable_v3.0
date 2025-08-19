#!/usr/bin/env python3
"""
01_sync_consolidado.py

Purpose:
- Ensure Source_Files/ exists with required inputs:
  - consolidado.json
  - Text_Processing_Rules.xlsx
  - Maestro.xlsx
  - processed_consolidado.db (created in step 02)

Behavior:
- Validates presence; prints clear instructions if missing.
- Optionally seeds minimal sample data when --seed is provided (dev/testing only).

This script does not download from remote by default (no URL provided).
"""
import json
from pathlib import Path
import argparse
from datetime import datetime

import os
import shutil
import tempfile
from typing import Optional, Dict

try:
    import requests  # used only when --download is requested
except Exception:
    requests = None


try:
    import openpyxl
except ImportError:
    openpyxl = None

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Source_Files"
SRC.mkdir(parents=True, exist_ok=True)

REQUIRED = [
    SRC / "consolidado.json",
    SRC / "Text_Processing_Rules.xlsx",
]


def seed_minimal():
    """Create minimal test consolidado.json only.
    NOTE: We never create Text_Processing_Rules.xlsx or Maestro.xlsx here.
    """
    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "records": [
            {"vin": "1HGCM82633A123456", "sku": "SKU-001", "price": 199.99, "brand": "BrandA", "maker": "Honda", "model": "Accord", "series": "EX"},
            {"vin": "1HGCM82633A654321", "sku": "SKU-002", "price": 249.99, "brand": "BrandB", "maker": "Honda", "model": "Accord", "series": "LX"},
            {"vin": "JTDKN3DU0A0123456", "sku": "SKU-003", "price": 299.99, "brand": "BrandC", "maker": "Toyota", "model": "Prius", "series": "III"},
        ]
    }
    with open(SRC / "consolidado.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
def load_config() -> Dict[str, str]:
    cfg_path = SRC / "config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def download_file(url: str, target: Path) -> None:
    """Download a file with visible progress and sensible timeouts.
    Uses separate connect/read timeouts to avoid hanging indefinitely.
    """
    if not requests:
        raise SystemExit("requests not installed; run 0_install_packages.bat")
    target.parent.mkdir(parents=True, exist_ok=True)

    import time
    import sys

    tmp_path = None
    try:
        # Separate timeouts: (connect, read)
        with requests.get(url, stream=True, timeout=(15, 60)) as r:
            r.raise_for_status()
            total = int(r.headers.get('Content-Length', 0))
            downloaded = 0
            last_log = 0.0
            chunk_size = 1024 * 1024  # 1 MB
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    tmp.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_log >= 1.0:
                        if total > 0:
                            pct = int(downloaded * 100 / total)
                            print(f"[INFO] Downloading... {downloaded/1e6:.1f}MB/{total/1e6:.1f}MB ({pct}%)", flush=True)
                        else:
                            print(f"[INFO] Downloaded {downloaded/1e6:.1f}MB", flush=True)
                        last_log = now
                tmp_path = Path(tmp.name)
        shutil.move(tmp_path, target)
    finally:
        # Clean up temp file on failure
        try:
            if tmp_path and Path(tmp_path).exists() and not Path(target).exists():
                Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass

    # Deprecated: creation now handled above with existence check (no overwrite)
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true", help="Create minimal sample Source_Files for testing")
    ap.add_argument("--download", action="store_true", help="Download consolidado.json from URL in Source_Files/config.json or CONSOLIDADO_URL env var")
    args = ap.parse_args()

    cfg = load_config()

    if args.seed:
        seed_minimal()

    # Optional download if requested
    if args.download:
        url = os.environ.get("CONSOLIDADO_URL") or cfg.get("consolidado_url")
        if not url:
            print("[ERROR] --download specified but no URL found. Set CONSOLIDADO_URL env var or Source_Files/config.json {\"consolidado_url\": ""...""}.")
            raise SystemExit(2)
        print(f"[INFO] Downloading consolidado.json from: {url}")
        try:
            download_file(url, SRC / "consolidado.json")
        except Exception as e:
            print("[ERROR] Download failed:", e)
            raise SystemExit(3)

    print("[INFO] Validating Source_Files contents...")
    missing = [p for p in REQUIRED if not p.exists()]

    if missing:
        print("[ERROR] Missing required files:")
        for m in missing:
            print(f"   - {m.relative_to(ROOT)}")
        print("\nPlease place these files into Source_Files/ or run with --seed for minimal test data.")
        raise SystemExit(1)

    print("[OK] Source_Files validation passed.")


if __name__ == "__main__":
    main()

