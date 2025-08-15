#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fixacar SKU Predictor - Portable Python v3.0
Main Entry Point for Portable Application

This is the main launcher for the portable Python version of the SKU Predictor.
It sets up the environment and launches the appropriate application mode.
"""

import sys
import os
import argparse

# Add the src directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def main():
    """Main entry point for the portable application"""

    parser = argparse.ArgumentParser(description='Fixacar SKU Predictor v3.0')
    parser.add_argument('--test', action='store_true',
                       help='Run minimal test version')
    parser.add_argument('--gui', action='store_true', default=True,
                       help='Run GUI version (default)')

    args = parser.parse_args()

    print("🚗 Fixacar SKU Predictor v3.0 - Portable Python")
    print("=" * 50)
    print(f"Working directory: {current_dir}")
    print(f"Python version: {sys.version}")
    print("=" * 50)

    try:
        if args.test:
            print("🧪 Running MINIMAL TEST version...")
            from minimal_test import main as test_main
            return test_main()
        else:
            print("🖥️ Running GUI application...")
            from main_app import main as app_main
            return app_main()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nThis might be because:")
        print("1. Required data files are missing (see DATA_SETUP.md)")
        print("2. Python environment is not properly set up")
        print("3. Some dependencies are missing")
        print("\nTrying minimal test instead...")

        try:
            from minimal_test import main as test_main
            return test_main()
        except Exception as e2:
            print(f"❌ Even minimal test failed: {e2}")
            input("Press Enter to exit...")
            return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)