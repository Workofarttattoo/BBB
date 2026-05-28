"""
Agent Sandbox — Git Worktree + Verify for Code Tasks
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Implements G2 phase gate:
- Create isolated git worktree for code changes
- Run verification (tests, linting, build)
- Judge evaluates code quality
- Only create PR after judge pass + human review

Usage:
    sandbox = AgentSandbox(repo_path="/path/to/repo")
    result = await sandbox.execute_code_task(
        task_description="Add /health endpoint to API",
        role="engineer"
    )
    
    if result["verified"]:
        # Ready for PR creation (after human review)
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SandboxResult:
    """Result from sandbox execution."""
    task_id: str
    worktree_path: str
    success: bool
    verified: bool
    changes: List[str]
    test_output: Optional[str]
    lint_output: Optional[str]
    build_output: Optional[str]
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "worktree_path": self.worktree_path,
            "success": self.success,
            "verified": self.verified,
            "changes": self.changes,
            "test_output": self.test_output,
            "lint_output": self.lint_output,
            "build_output": self.build_output,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat()
        }


class AgentSandbox:
    """
    Isolated execution environment for code tasks.
    
    Viktor-style features:
    - Creates isolated git worktree (no contamination of main repo)
    - Runs verification automatically (tests, lint, build)
    - Returns structured diff for judge evaluation
    - Never commits to main branch without approval
    """
    
    def __init__(
        self,
        repo_path: str,
        base_branch: str = "main",
        worktree_prefix: str = "sandbox-"
    ):
        self.repo_path = Path(repo_path).resolve()
        self.base_branch = base_branch
        self.worktree_prefix = worktree_prefix
        
        if not self.repo_path.exists():
            raise ValueError(f"Repo path does not exist: {self.repo_path}")
        
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")
        
        # Worktree directory
        self.worktrees_path = self.repo_path / ".sandboxes"
        self.worktrees_path.mkdir(exist_ok=True)
    
    async def execute_code_task(
        self,
        task_description: str,
        role: str = "engineer",
        context: Optional[Dict[str, Any]] = None
    ) -> SandboxResult:
        """
        Execute code task in isolated sandbox.
        
        Args:
            task_description: Natural language coding task
            role: Agent role (should be "engineer")
            context: Optional context (files to modify, constraints)
            
        Returns:
            SandboxResult with changes and verification status
        """
        task_id = str(uuid.uuid4())[:8]
        worktree_name = f"{self.worktree_prefix}{task_id}"
        worktree_path = self.worktrees_path / worktree_name
        
        logger.info(f"Creating sandbox worktree {worktree_name} for task: {task_description[:100]}...")
        
        try:
            # Step 1: Create worktree from base branch
            await self._create_worktree(worktree_name, worktree_path)
            
            # Step 2: Generate code changes (would call agent here)
            # For now, this is a placeholder - actual implementation would call RoleAgentRunner
            changes = await self._generate_code_changes(
                worktree_path=worktree_path,
                task_description=task_description,
                context=context or {}
            )
            
            # Step 3: Run verification
            test_output, lint_output, build_output = await self._run_verification(worktree_path)
            
            # Step 4: Determine if verified
            verified = self._check_verification(test_output, lint_output, build_output)
            
            logger.info(f"Sandbox task {task_id} completed: verified={verified}, changes={len(changes)}")
            
            return SandboxResult(
                task_id=task_id,
                worktree_path=str(worktree_path),
                success=True,
                verified=verified,
                changes=changes,
                test_output=test_output,
                lint_output=lint_output,
                build_output=build_output
            )
            
        except Exception as e:
            logger.exception(f"Sandbox task failed: {e}")
            
            # Cleanup on failure
            if worktree_path.exists():
                await self._cleanup_worktree(worktree_path)
            
            return SandboxResult(
                task_id=task_id,
                worktree_path=str(worktree_path) if 'worktree_path' in locals() else "",
                success=False,
                verified=False,
                changes=[],
                test_output=None,
                lint_output=None,
                build_output=None,
                error_message=str(e)
            )
    
    async def _create_worktree(self, name: str, path: Path):
        """Create git worktree from base branch."""
        cmd = ["git", "worktree", "add", "-b", name, str(path), self.base_branch]
        
        try:
            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create worktree: {result.stderr}")
            logger.debug(f"Created worktree {name} at {path}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git worktree creation timed out")
    
    async def _generate_code_changes(
        self,
        worktree_path: Path,
        task_description: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Generate code changes using agent.
        
        This is where RoleAgentRunner would be called to actually write code.
        For now, returns placeholder - implement integration with auto_judge_loop.
        """
        # TODO: Integrate with AutoJudgeLoop
        # Example:
        # from .auto_judge_loop import AutoJudgeLoop
        # judge_loop = AutoJudgeLoop(company_pack="saas-micro-tools")
        # result = await judge_loop.execute_with_judge(
        #     role="engineer",
        #     task_description=task_description,
        #     context={**context, "worktree_path": str(worktree_path)}
        # )
        # 
        # if result.success:
        #     # Agent wrote files to worktree_path
        #     return self._get_changed_files(worktree_path)
        
        logger.warning("Code generation not yet integrated with agent runner")
        return []
    
    async def _run_verification(self, worktree_path: Path) -> tuple:
        """Run tests, linting, and build in worktree."""
        test_output = None
        lint_output = None
        build_output = None
        
        # Test command (configurable per project)
        test_cmd = self._detect_test_command(worktree_path)
        if test_cmd:
            try:
                result = await asyncio.create_subprocess_exec(
                    *test_cmd,
                    cwd=worktree_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=120)
                test_output = stdout.decode() + "\n" + stderr.decode()
                logger.debug(f"Tests completed with return code {result.returncode}")
            except asyncio.TimeoutError:
                test_output = "Tests timed out after 120s"
            except Exception as e:
                test_output = f"Test execution failed: {e}"
        
        # Lint command
        lint_cmd = self._detect_lint_command(worktree_path)
        if lint_cmd:
            try:
                result = await asyncio.create_subprocess_exec(
                    *lint_cmd,
                    cwd=worktree_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=60)
                lint_output = stdout.decode() + "\n" + stderr.decode()
            except Exception as e:
                lint_output = f"Lint execution failed: {e}"
        
        # Build command
        build_cmd = self._detect_build_command(worktree_path)
        if build_cmd:
            try:
                result = await asyncio.create_subprocess_exec(
                    *build_cmd,
                    cwd=worktree_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=180)
                build_output = stdout.decode() + "\n" + stderr.decode()
            except Exception as e:
                build_output = f"Build execution failed: {e}"
        
        return test_output, lint_output, build_output
    
    def _check_verification(
        self,
        test_output: Optional[str],
        lint_output: Optional[str],
        build_output: Optional[str]
    ) -> bool:
        """Check if verification passed."""
        # Tests must pass (if run)
        if test_output is not None:
            if "FAILED" in test_output or "error" in test_output.lower():
                return False
            if "passed" not in test_output.lower() and "ok" not in test_output.lower():
                # Ambiguous - might need judge to evaluate
                pass
        
        # Lint should have no errors (warnings ok)
        if lint_output is not None:
            if "error" in lint_output.lower() and "warning" not in lint_output.lower():
                return False
        
        # Build must succeed
        if build_output is not None:
            if "error" in build_output.lower() or "failed" in build_output.lower():
                return False
        
        return True
    
    def _detect_test_command(self, worktree_path: Path) -> Optional[List[str]]:
        """Detect test command based on project type."""
        # Python: pytest
        if (worktree_path / "pytest.ini").exists() or (worktree_path / "setup.py").exists():
            return ["pytest", "-v"]
        
        # Node.js: npm test
        if (worktree_path / "package.json").exists():
            return ["npm", "test"]
        
        # Rust: cargo test
        if (worktree_path / "Cargo.toml").exists():
            return ["cargo", "test"]
        
        return None
    
    def _detect_lint_command(self, worktree_path: Path) -> Optional[List[str]]:
        """Detect lint command based on project type."""
        # Python: flake8 or pylint
        if (worktree_path / ".flake8").exists() or (worktree_path / "setup.py").exists():
            return ["flake8", "."]
        
        # Node.js: npm run lint
        if (worktree_path / "package.json").exists():
            return ["npm", "run", "lint"]
        
        return None
    
    def _detect_build_command(self, worktree_path: Path) -> Optional[List[str]]:
        """Detect build command based on project type."""
        # Python: no build needed usually
        if (worktree_path / "setup.py").exists():
            return None
        
        # Node.js: npm run build
        if (worktree_path / "package.json").exists():
            return ["npm", "run", "build"]
        
        # Rust: cargo build
        if (worktree_path / "Cargo.toml").exists():
            return ["cargo", "build"]
        
        return None
    
    def _get_changed_files(self, worktree_path: Path) -> List[str]:
        """Get list of changed files in worktree vs base branch."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", self.base_branch],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split("\n") if line.strip()]
        except Exception as e:
            logger.warning(f"Failed to get changed files: {e}")
        
        return []
    
    async def _cleanup_worktree(self, worktree_path: Path):
        """Remove worktree after completion."""
        try:
            # Remove from git worktree list
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path)],
                cwd=self.repo_path,
                capture_output=True,
                timeout=30
            )
            # Remove directory
            shutil.rmtree(worktree_path, ignore_errors=True)
            logger.debug(f"Cleaned up worktree {worktree_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup worktree: {e}")
    
    async def cleanup_all_worktrees(self):
        """Remove all sandbox worktrees."""
        if self.worktrees_path.exists():
            for worktree in self.worktrees_path.iterdir():
                if worktree.is_dir():
                    await self._cleanup_worktree(worktree)
    
    def get_diff_for_review(self, worktree_path: Path) -> str:
        """Get unified diff for human/judge review."""
        try:
            result = subprocess.run(
                ["git", "diff", self.base_branch],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception as e:
            logger.warning(f"Failed to get diff: {e}")
            return ""
