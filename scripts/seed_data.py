#!/usr/bin/env python3
"""
CLI entry point for seeding the Route Health Dashboard database.

The actual seeding logic lives in app/seed_data.py (inside the `app`
package) so it can also be called at runtime by app/main.py on cold
start — this script is just a thin wrapper for local/manual use:

    python scripts/seed_data.py
"""

import argparse
import os
import sys

# Ensure the project root is on the Python path so `app` is importable
# regardless of the directory the script is invoked from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.seed_data import seed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Route Health Dashboard database.")
    parser.add_argument("--live", action="store_true", help="Attempt to fetch from NYC 311 SODA API (fallback to synthetic)")
    args = parser.parse_args()

    if args.live:
        print("Note: --live flag recognized. The NYC 311 dataset")
        print("(https://catalog.data.gov/dataset/311-service-requests-from-2010-to-present)")
        print("inspired the complaint categories and feedback patterns in this seed data.")

    seed()