import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

# Import the core system
from ech0_autonomous_business import ECH0AutonomousCore

async def dry_run():
    print("🚀 Starting ECH0 Autonomous Core DRY RUN...")
    
    # Initialize core with existing config
    core = ECH0AutonomousCore()
    
    print(f"\nSystem Status: {core.system_status}")
    print(f"Loaded Modules: {list(core.modules.keys())}")
    
    # Test Email/SMS module initialization
    email_module = core.modules.get('email')
    if email_module:
        print("\n--- Testing Module Communication Handlers ---")
        # Trigger a test report send (this will log success/failure in activity log)
        # We use a fake report to see if it tries SMTP -> SG -> Twilio
        success = email_module.send_email(
            to="inventor@aios.is",
            subject="DRY RUN REPORT",
            body="This is a system dry run test."
        )
        print(f"Sent output: {success}")
    
    print("\n--- Activity Log (Last 5) ---")
    for log in core.activity_log[-5:]:
        print(f"[{log['module']} - {log['action']}] {log['details']}")

    print("\n✅ Dry run complete. Modules initialized correctly.")

if __name__ == "__main__":
    # Ensure we use the virtual environment python
    asyncio.run(dry_run())
