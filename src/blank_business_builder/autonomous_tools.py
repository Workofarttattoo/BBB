"""
Autonomous Tools for Echo
=========================
Tools for the autonomous agents to interact with the world:
- Web Search (DuckDuckGo)
- Code Execution (Shell)
- File Management
"""

import os
import subprocess
import glob
from typing import List, Dict, Optional
from duckduckgo_search import DDGS

class AutonomousTools:
    
    @staticmethod
    def web_search(query: str, max_results: int = 5) -> List[Dict]:
        """Search the web using DuckDuckGo."""
        results = []
        try:
            with DDGS() as ddgs:
                # ddgs.text returns an iterator, consume it
                generator = ddgs.text(query, max_results=max_results)
                if generator:
                    results = list(generator)
        except Exception as e:
            print(f"[ERROR] Web search failed: {e}")
        return results

    # Allowlisted commands that autonomous agents may execute
    ALLOWED_COMMANDS = frozenset({
        "git", "python", "python3", "pip", "node", "npm", "ls", "cat",
        "head", "tail", "wc", "grep", "find", "curl", "wget",
    })

    @classmethod
    def run_shell_command(cls, command: str, cwd: str = ".") -> Dict:
        """Run a shell command and return output.

        Security: uses ``shell=False`` with an explicit allowlist to
        prevent shell-injection attacks.  Only the first token (the
        executable) is checked against the allowlist.
        """
        import shlex

        try:
            parts = shlex.split(command)
        except ValueError as e:
            return {"error": f"Invalid command syntax: {e}", "returncode": -1}

        if not parts:
            return {"error": "Empty command", "returncode": -1}

        executable = os.path.basename(parts[0])
        if executable not in cls.ALLOWED_COMMANDS:
            return {
                "error": f"Command '{executable}' is not in the allowlist",
                "returncode": -1,
            }

        try:
            result = subprocess.run(
                parts,
                shell=False,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out", "returncode": -1}
        except Exception as e:
            return {"error": str(e), "returncode": -1}

    @staticmethod
    def list_files(pattern: str, recursive: bool = False) -> List[str]:
        """List files matching a pattern."""
        return glob.glob(pattern, recursive=recursive)

    @staticmethod
    def read_file(filepath: str) -> str:
        """Read content of a file."""
        if not os.path.exists(filepath):
            return "File not found."
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    def write_file(filepath: str, content: str) -> bool:
        """Write content to a file."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[ERROR] Write failed: {e}")
            return False
