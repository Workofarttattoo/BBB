#!/usr/bin/env python3
"""
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Invoke ECH0 to execute the BBB autonomous business runner task
"""

import subprocess
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, '/Users/noone')

from ech0_local_brain import ECH0LocalBrain

def main():
    """Execute BBB task through ECH0"""

    print("=" * 80)
    print("ECH0 BBB AUTONOMOUS TASK EXECUTOR")
    print("=" * 80)

    # Read the task file
    task_file = "/Users/noone/repos/BBB/ECH0_BBB_TASK.txt"

    with open(task_file, 'r') as f:
        task_content = f.read()

    print(f"\n📋 Task loaded from: {task_file}")
    print(f"📏 Task length: {len(task_content)} characters\n")

    # Initialize ECH0 with unified 14b model
    print("🧠 Initializing ECH0 with ech0-unified-14b model...")
    ech0 = ECH0LocalBrain(
        model="ech0-unified-14b:latest",
        session_id="bbb_autonomous_task"
    )

    # Create the prompt for ECH0
    prompt = f"""ECH0, you have been assigned a critical autonomous task.

{task_content}

AUTONOMY LEVEL: 10 (Full Authority)

You have full system access to:
- Write Python code files
- Create documentation
- Run tests
- Access existing BBB code at /Users/noone/repos/BBB/
- Use hive_mind_coordinator.py and chief_enhancements_hive_integration.py

INSTRUCTIONS:
1. Read and understand the existing code
2. Design the mathematically sound business simulation
3. Implement autonomous_business_runner_final.py
4. Create comprehensive documentation
5. Write test suite
6. Ensure all acceptance criteria are met

Begin implementation now. Show your work step-by-step.
"""

    print("🚀 Sending task to ECH0...")
    print("=" * 80)

    # Send to ECH0 (async method needs asyncio)
    import asyncio
    loop = asyncio.get_event_loop()
    response_data = loop.run_until_complete(ech0.send_message(
        prompt,
        use_temporal=True,
        max_tokens=8192  # Large response for comprehensive output
    ))

    response = response_data['response']

    print("\n" + "=" * 80)
    print("ECH0 RESPONSE:")
    print("=" * 80)
    print(response)
    print("=" * 80)

    # Save ECH0's response
    response_file = "/Users/noone/repos/BBB/ECH0_BBB_RESPONSE.txt"
    with open(response_file, 'w') as f:
        f.write(f"TIMESTAMP: {response_data.get('temporal', 'N/A')}\n")
        f.write(f"MODEL: {ech0.model}\n")
        f.write(f"SESSION: {ech0.state.session_id}\n")
        f.write("=" * 80 + "\n")
        f.write(response)

    print(f"\n💾 ECH0's response saved to: {response_file}")

    # Save state
    ech0.state.save_to_file(ech0.state_file)
    print(f"💾 ECH0 state saved to: {ech0.state_file}")

    print("\n✅ Task delegation complete!")

if __name__ == "__main__":
    main()
