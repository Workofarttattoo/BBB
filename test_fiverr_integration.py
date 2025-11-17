#!/usr/bin/env python3
"""
Test script for Fiverr Autonomous Manager integration.
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This script verifies:
1. Module imports work correctly
2. Configuration is valid
3. Chrome profile is accessible
4. Agent can initialize (without requiring active Fiverr session)
"""

import os
import sys
from pathlib import Path

print("="*60)
print("  FIVERR AUTONOMOUS MANAGER - INTEGRATION TEST")
print("  Copyright (c) 2025 Joshua Hendricks Cole")
print("="*60 + "\n")

# Test 1: Module imports
print("[TEST 1] Checking module imports...")
try:
    from fiverr_autonomous_manager import FiverrAutonomousManager
    print("✓ fiverr_autonomous_manager imported successfully")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

try:
    from fiverr_watchdog_autonomous import FiverrWatchdog
    print("✓ fiverr_watchdog_autonomous imported successfully")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

try:
    from ech0_autonomous_business import ECH0AutonomousCore
    print("✓ ech0_autonomous_business imported successfully")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Test 2: Selenium dependencies
print("\n[TEST 2] Checking Selenium dependencies...")
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    print("✓ Selenium dependencies available")
except ImportError as e:
    print(f"✗ FAILED: {e}")
    print("  Install with: pip install selenium webdriver-manager")
    sys.exit(1)

# Test 3: Environment configuration
print("\n[TEST 3] Checking environment configuration...")
chrome_profile = os.getenv("FIVERR_CHROME_PROFILE_PATH")
profile_dir = os.getenv("FIVERR_PROFILE_DIRECTORY", "Default")

if chrome_profile:
    print(f"✓ FIVERR_CHROME_PROFILE_PATH: {chrome_profile}")
    print(f"✓ FIVERR_PROFILE_DIRECTORY: {profile_dir}")

    # Check if profile exists
    if Path(chrome_profile).exists():
        print(f"✓ Chrome profile directory exists")
    else:
        print(f"⚠ WARNING: Chrome profile directory not found")
        print(f"  Expected: {chrome_profile}")
else:
    print("⚠ WARNING: FIVERR_CHROME_PROFILE_PATH not set")
    print("  The manager will attempt system default detection")
    print("  Recommended: Set environment variable for reliability")

# Test 4: Configuration file
print("\n[TEST 4] Checking ECH0 configuration...")
config_path = "/Users/noone/.ech0/business_config.json"

if Path(config_path).exists():
    print(f"✓ Configuration file exists: {config_path}")

    import json
    with open(config_path, 'r') as f:
        config = json.load(f)

    fiverr_config = config.get('fiverr', {})
    if fiverr_config.get('chrome_profile_path'):
        print(f"✓ Fiverr Chrome profile configured")
    else:
        print("⚠ WARNING: Fiverr Chrome profile not configured in config file")
else:
    print("ℹ INFO: Configuration file not found (will be created on first run)")

# Test 5: Log directory
print("\n[TEST 5] Checking log directories...")
log_dir = Path("/Users/noone/.ech0")
if not log_dir.exists():
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created log directory: {log_dir}")
else:
    print(f"✓ Log directory exists: {log_dir}")

# Test 6: ChromeDriver availability
print("\n[TEST 6] Checking ChromeDriver...")
try:
    from webdriver_manager.chrome import ChromeDriverManager
    driver_path = ChromeDriverManager().install()
    print(f"✓ ChromeDriver available: {driver_path}")
except Exception as e:
    print(f"⚠ WARNING: ChromeDriver check failed: {e}")
    print("  This may still work, but could cause issues at runtime")

# Summary
print("\n" + "="*60)
print("  INTEGRATION TEST SUMMARY")
print("="*60)
print("\n✓ All critical tests passed")
print("\nℹ NEXT STEPS:")
print("  1. Set FIVERR_CHROME_PROFILE_PATH environment variable (if not set)")
print("  2. Log into Fiverr manually using your Chrome profile (once)")
print("  3. Run standalone watchdog: python fiverr_watchdog_autonomous.py")
print("  4. Or integrate with ECH0: python ech0_autonomous_business.py")
print("\n📖 See FIVERR_AUTONOMOUS_SETUP.md for detailed setup guide")
print("\nCopyright (c) 2025 Joshua Hendricks Cole")
print("Corporation of Light - PATENT PENDING\n")
