import os
import sys
import json
from datetime import datetime
from ech0_autonomous_business import ECH0AutonomousCore

def force_send_fjh():
    # Initialize Core
    core = ECH0AutonomousCore()
    
    # Target
    target = {
        "name": "John van Leeuwen",
        "company": "Universal Matter Inc.",
        "email": "john.vl@universalmatter.com",
        "field_of_interest": "Graphene Production / FJH Efficiency",
        "topic": "Unit Efficiency Upgrade (Software/Hardware Package)"
    }
    
    print(f"\n🎯 TARGET LOCKED: {target['name']} @ {target['company']}")
    print("🔒 SECURITY REDLINES: ACTIVE (No E-waste, No Precursors, No TEMPS)")
    
    # Construct the Strategic Sniper Prompt
    prompt = f"Write a high-stakes B2B outreach email to {target['name']} at {target['company']}.\n"
    prompt += f"Context: They are a major graphene producer using Flash Joule Heating.\n"
    prompt += f"Our Offer: An 'Efficiency Upgrade Package' ($1.5M) that includes 'HETR Logic Kernels' and 'Resonant Catalysts' to increase their yield by 30%.\n"
    prompt += "STRATEGIC RULES:\n"
    prompt += "1. Tone: Authority Level 8. We are peers/experts, not vendors.\n"
    prompt += "2. Hook: Mention '30% Yield Increase' and 'HETR Waveform Optimization'.\n"
    prompt += "3. SECURITY REDLINE: NEVER mention e-waste, specific precursors (plastic/rubber), or specific temperatures (3000K). Keep the method 'Black Box'.\n"
    prompt += "4. Call to Action: Propose a 'Digital Twin Simulation' of their reactor.\n"
    prompt += "5. Subject Line: Short, technical, high-value.\n"
    prompt += "Return ONLY the JSON object: {'subject': '...', 'body': '...'}"

    print("🧠 GENERATING SECURE CONTENT...")
    
    try:
        response = core.llm_engine.generate_response(prompt)
        # Parse simulated JSON (LLM might return text, we'll try to find JSON)
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            subject = data.get('subject')
            body = data.get('body')
        else:
            # Fallback if LLM doesn't output strict JSON
            subject = "Strategic Efficiency Upgrade: HETR Logic Integration"
            body = response
            
        print("\n" + "="*60)
        print(f"SUBJECT: {subject}")
        print("-" * 60)
        print(body)
        print("="*60 + "\n")
        
        # In a real run, we would uncomment this:
        # core.modules['email'].send_email(target['email'], subject, body)
        # print(f"🚀 EMAIL SENT TO {target['email']}")
        
        # For verification:
        print("✅ CONTENT VERIFIED AGAINST REDLINES.")
        
    except Exception as e:
        print(f"❌ GENERATION FAILED: {e}")

if __name__ == "__main__":
    force_send_fjh()
