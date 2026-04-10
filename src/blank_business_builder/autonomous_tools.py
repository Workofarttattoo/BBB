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
import asyncio
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

    @staticmethod
    def run_shell_command(command: str, cwd: str = ".") -> Dict:
        """Run a shell command and return output."""
        try:
            result = subprocess.run(
                command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command time out", "returncode": -1}
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
            with open(filepath, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    async def async_read_file(filepath: str) -> str:
        """
        Read content of a file asynchronously.
        # ⚡ Bolt Optimization: Uses run_in_executor to prevent blocking the event loop
        # during file I/O operations, which is critical for async server performance.
        """
        if not os.path.exists(filepath):
            return "File not found."

        loop = asyncio.get_running_loop()
        try:
            # We don't use aiofiles because it's a 3rd party dependency
            # and might not be available. We use the built-in run_in_executor
            def _read_inner():
                with open(filepath, "r") as f:
                    return f.read()

            return await loop.run_in_executor(None, _read_inner)
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    def write_file(filepath: str, content: str) -> bool:
        """Write content to a file."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[ERROR] Write failed: {e}")
            return False

    @staticmethod
    async def async_write_file(filepath: str, content: str) -> bool:
        """
        Write content to a file asynchronously.
        # ⚡ Bolt Optimization: Uses run_in_executor to prevent blocking the event loop
        # during file I/O operations, which is critical for async server performance.
        """
        loop = asyncio.get_running_loop()

        def _write_inner():
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"[ERROR] Async write failed: {e}")
                return False

        return await loop.run_in_executor(None, _write_inner)
