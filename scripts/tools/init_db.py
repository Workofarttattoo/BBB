#!/usr/bin/env python3
"""
Initialize database for Better Business Builder.
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from blank_business_builder.database import init_db
from blank_business_builder.config import settings

def main():
    print(f"Initializing database at: {settings.DATABASE_URL}")
    engine = init_db(settings.DATABASE_URL)
    print("Database schema created successfully.")

if __name__ == "__main__":
    main()
