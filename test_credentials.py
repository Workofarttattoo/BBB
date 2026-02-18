import os
import sys
from pathlib import Path

# Fix path to import from src
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from src.blank_business_builder.config import settings
    from src.blank_business_builder.integrations import IntegrationFactory
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def test_twilio():
    print("\n--- Testing Twilio Integration ---")
    if not settings.TWILIO_ACCOUNT_SID:
        print("❌ TWILIO_ACCOUNT_SID not found in environment.")
        return
    
    print(f"SID found: {settings.TWILIO_ACCOUNT_SID[:5]}...")
    service = IntegrationFactory.get_twilio_service()
    
    if service.client:
        print("✅ Twilio client initialized successfully.")
        # Try a safe API call (e.g., fetch account info)
        try:
            account = service.client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
            print(f"✅ Connection successful! Account Name: {account.friendly_name}")
        except Exception as e:
            print(f"❌ Twilio API Connection failed: {e}")
    else:
        print("❌ Twilio client failed to initialize.")

def test_sendgrid():
    print("\n--- Testing SendGrid Integration ---")
    if not settings.SENDGRID_API_KEY:
        print("⚠️  SENDGRID_API_KEY not found (Using simulation).")
    else:
        print(f"Key found: {settings.SENDGRID_API_KEY[:5]}...")
        
    service = IntegrationFactory.get_sendgrid_service()
    if service.client:
        print("✅ SendGrid service initialized.")
    else:
        print("⚠️  SendGrid service in simulation mode.")

def test_twitter():
    print("\n--- Testing Twitter Integration ---")
    if not settings.TWITTER_CONSUMER_KEY:
        print("❌ TWITTER_CONSUMER_KEY not found in environment.")
        return
    
    print(f"Consumer Key found: {settings.TWITTER_CONSUMER_KEY[:5]}...")
    
    # Debug info
    from src.blank_business_builder.integrations import TWEEPY_AVAILABLE
    print(f"TWEEPY_AVAILABLE: {TWEEPY_AVAILABLE}")
    
    try:
        service = IntegrationFactory.get_twitter_service()
        if service.client:
            print("✅ Twitter client initialized successfully.")
            # ... rest of the logic ...
    except Exception as e:
        print(f"❌ Initialization Crashed: {e}")
        return

    if service.client:
        # Try a safe API call (e.g., fetch me)
        try:
            me = service.client.get_me()
            if me.data:
                print(f"✅ Connection successful! User: @{me.data.username}")
            else:
                print("⚠️  Connection established but could not fetch user profile.")
        except Exception as e:
            print(f"❌ Twitter API Connection failed: {e}")
    else:
        print(f"❌ Twitter client failed to initialize (Client is None). KEYS: {bool(settings.TWITTER_CONSUMER_KEY)}/{bool(settings.TWITTER_CONSUMER_SECRET)}")

if __name__ == "__main__":
    print(f"Loading config from: {Path('.env').resolve()}")
    test_twilio()
    test_sendgrid()
    test_twitter()
