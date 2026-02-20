"""
Autonomous Developer Agent
==========================
Agent capable of writing code, running tests, and managing the repository.
"""

import os
import time
from .autonomous_tools import AutonomousTools

class AutonomousDeveloper:
    def __init__(self, core_system):
        self.core = core_system
        self.tools = AutonomousTools()

    def develop_feature(self, task_description: str, target_file: str = None):
        """
        Develop a feature or fix a bug.
        1. Read existing code (if target_file provided).
        2. Plan implementation.
        3. Write code.
        4. Run tests (if applicable).
        """
        print(f"👨‍💻 DEV: Starting task: {task_description}")
        
        current_code = ""
        if target_file and os.path.exists(target_file):
            current_code = self.tools.read_file(target_file)
            
        # Prompt LLM to write code
        prompt = f"""
        You are an expert Python developer.
        Task: {task_description}
        Target File: {target_file}
        
        Existing Code:
        ```python
        {current_code[-2000:]}  # Last 2000 chars for context
        ```
        
        Return the COMPLETE new code for the file. 
        Wrap code in ```python blocks.
        """
        
        if self.core.llm_engine:
            response = self.core.llm_engine.generate_response(prompt)
            
            # Extract code block
            code = self._extract_code(response)
            if code:
                if target_file:
                    self.tools.write_file(target_file, code)
                    print(f"✅ DEV: Updated {target_file}")
                    
                    # Optional: Syntax check
                    check = self.tools.run_shell_command(f"python3 -m py_compile {target_file}")
                    if check['returncode'] == 0:
                        print(f"✅ DEV: Syntax check passed for {target_file}")
                    else:
                        print(f"❌ DEV: Syntax error in {target_file}: {check['stderr']}")
                else:
                    print(f"⚠️ DEV: No target file specified. Code generated but not saved.")
            else:
                print("❌ DEV: Failed to generate valid code.")

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown blocks."""
        if "```python" in text:
            start = text.find("```python") + 9
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        return text  # Fallback: assume raw code if no blocks (risky)
