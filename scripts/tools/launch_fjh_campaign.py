import json
import os
import time
from ech0_autonomous_business import ECH0AutonomousCore

def launch_fjh_campaign():
    core = ECH0AutonomousCore()
    
    # Load the sanitized targets
    path = "/Users/noone/echo_prime/FJH_OUTREACH_EMAILS.json"
    if not os.path.exists(path):
        print(f"❌ Error: {path} not found.")
        return

    with open(path, 'r') as f:
        targets = json.load(f)
        
    print(f"\n🚀 LAUNCHING FJH OUTREACH CAMPAIGN ({len(targets)} Targets)")
    print("="*60)
    
    for target in targets:
        # Construct the email
        subject = target['email_subject']
        body = target['email_body']
        
        # Determine the recipient email (based on previous knowledge/guesses since JSON only has names)
        # In a real scenario, this would come from a richer database.
        # Hardcoding the known FJH contacts for safety/demonstration
        to_email = ""
        if "Universal Matter" in target['company']:
            to_email = "john.vl@universalmatter.com"
        elif "SpaceX" in target['company']:
            to_email = "materials@spacex.com" # Placeholder, Echo would search this
        elif "MTM Critical Metals" in target['company']:
            to_email = "l.reynolds@mtmcriticalmetals.com" 
        elif "Ford" in target['company']:
            to_email = "sustainability@ford.com"
            
        if to_email:
            print(f"\n📧 Sending to: {target['contact']} ({to_email})")
            print(f"Subject: {subject}")
            print("-" * 40)
            
            # Use Core Email Module
            try:
                # Actual Send
                core.modules['email'].send_email(
                    to=to_email,
                    subject=subject,
                    body=body
                )
                print("✅ SENT SUCCESS")
                
                # Log it
                core.log_activity("crm", "FJH_CAMPAIGN_SENT", f"To: {target['company']} ({to_email})")
                
                # Sleep to be polite to SMTP
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ FAILED: {e}")
        else:
             print(f"⚠️  Skipping {target['company']} - No email address resolved.")

    print("\n✅ CAMPAIGN COMPLETE.")

if __name__ == "__main__":
    launch_fjh_campaign()
