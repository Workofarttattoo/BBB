"""
Git worktree sandbox for agent code tasks (Viktor PR pattern MVP).

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

BBB_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_WORKSPACE = BBB_ROOT / "workspace"


@dataclass
class SandboxResult:
    task_id: str
    worktree_path: str
    branch: str
    verify_ok: bool
    verify_output: str

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "worktree_path": self.worktree_path,
            "branch": self.branch,
            "verify_ok": self.verify_ok,
            "verify_output": self.verify_output[:4000],
        }


class AgentSandbox:
    """Local subprocess sandbox using git worktrees."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        workspace_root: Optional[Path] = None,
    ):
        self.repo_root = Path(repo_root or BBB_ROOT)
        self.workspace_root = Path(workspace_root or os.getenv("BBB_SANDBOX_ROOT", str(DEFAULT_WORKSPACE)))
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, task_id: str, base_ref: str = "HEAD") -> Path:
        safe_id = task_id.replace("/", "-").replace(" ", "-")[:48]
        branch = f"agent/{safe_id}"
        path = self.workspace_root / safe_id
        if path.exists():
            return path
        cmd = ["git", "worktree", "add", "-B", branch, str(path), base_ref]
        subprocess.run(cmd, cwd=self.repo_root, check=True, capture_output=True, text=True)
        logger.info("Created worktree %s on branch %s", path, branch)
        return path

    def run_verify(self, worktree_path: Path, fast: bool = True) -> tuple[bool, str]:
        script = self.repo_root / "scripts" / "agent-verify.sh"
        if not script.is_file():
            return False, "agent-verify.sh missing"
        args = ["bash", str(script)]
        if fast:
            args.append("--fast")
        proc = subprocess.run(
            args,
            cwd=worktree_path,
            capture_output=True,
            text=True,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, output

    def run_task(self, task_id: str, fast_verify: bool = True) -> SandboxResult:
        path = self.create_worktree(task_id)
        branch = f"agent/{task_id.replace('/', '-').replace(' ', '-')[:48]}"
        ok, output = self.run_verify(path, fast=fast_verify)
        return SandboxResult(
            task_id=task_id,
            worktree_path=str(path),
            branch=branch,
            verify_ok=ok,
            verify_output=output,
        )

    def remove_worktree(self, task_id: str) -> None:
        safe_id = task_id.replace("/", "-").replace(" ", "-")[:48]
        path = self.workspace_root / safe_id
        if not path.exists():
            return
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(path)],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
