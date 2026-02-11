import sys
from pathlib import Path
import asyncio
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.blank_business_builder.all_features_implementation import MobileAppBuilder, MobilePlatform

def test_build_app_ios():
    """Test building an iOS app."""
    builder = MobileAppBuilder()
    config = {"name": "Test App", "bundle_id": "com.test.app"}

    # Run async method synchronously
    result = asyncio.run(builder.build_app(MobilePlatform.IOS, config))

    assert result["platform"] == "ios"
    assert result["app_id"] == "com.betterbusinessbuilder.ios"
    assert result["version"] == "1.0.0"
    assert result["build_status"] == "success"
    assert result["download_url"] == "https://builds.betterbusinessbuilder.com/ios/latest.zip"

def test_build_app_android():
    """Test building an Android app."""
    builder = MobileAppBuilder()
    config = {"name": "Test App", "package_name": "com.test.app"}

    # Run async method synchronously
    result = asyncio.run(builder.build_app(MobilePlatform.ANDROID, config))

    assert result["platform"] == "android"
    assert result["app_id"] == "com.betterbusinessbuilder.android"
    assert result["version"] == "1.0.0"
    assert result["build_status"] == "success"
    assert result["download_url"] == "https://builds.betterbusinessbuilder.com/android/latest.zip"

def test_build_app_structure():
    """Verify the returned dictionary structure."""
    builder = MobileAppBuilder()

    result = asyncio.run(builder.build_app(MobilePlatform.IOS, {}))

    expected_keys = {"platform", "app_id", "version", "build_status", "download_url"}
    assert set(result.keys()) == expected_keys
