"""Job class for representing individual jobs."""

import os
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


@dataclass
class JobResult:
    """Result of a job execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    error_message: Optional[str] = None


@dataclass
class Job:
    """Represents a single job to be executed."""
    name: str
    repo_url: str
    commit: str
    script: str
    work_dir: Optional[Path] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[int] = 300  # 5 minutes default
    
    def __post_init__(self):
        """Initialize work directory if not provided."""
        if self.work_dir is None:
            self.work_dir = Path(tempfile.mkdtemp(prefix=f"job_{self.name}_"))
        else:
            self.work_dir = Path(self.work_dir)
            self.work_dir.mkdir(parents=True, exist_ok=True)
    
    def clone_repository(self) -> None:
        """Clone the repository to the work directory."""
        logger.info(f"Cloning repository {self.repo_url} to {self.work_dir}")
        try:
            # Clone the repository
            repo = Repo.clone_from(self.repo_url, self.work_dir)
            logger.info(f"Repository cloned successfully")
            
            # Checkout the specific commit
            logger.info(f"Checking out commit {self.commit}")
            repo.git.checkout(self.commit)
            logger.info(f"Checked out commit {self.commit}")
            
        except GitCommandError as e:
            raise RuntimeError(f"Failed to clone/checkout repository: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during repository operations: {e}")
    
    def execute_script(self) -> JobResult:
        """Execute the job script in the work directory."""
        logger.info(f"Executing script for job {self.name}")
        
        # Prepare environment variables
        env = os.environ.copy()
        env.update(self.env_vars)
        
        try:
            # Execute the script
            result = subprocess.run(
                self.script,
                shell=True,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env
            )
            
            success = result.returncode == 0
            
            if success:
                logger.info(f"Job {self.name} completed successfully")
            else:
                logger.error(f"Job {self.name} failed with exit code {result.returncode}")
            
            return JobResult(
                success=success,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )
            
        except subprocess.TimeoutExpired:
            error_msg = f"Job {self.name} timed out after {self.timeout} seconds"
            logger.error(error_msg)
            return JobResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"Failed to execute script: {e}"
            logger.error(error_msg)
            return JobResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=error_msg
            )
    
    def run(self) -> JobResult:
        """Run the complete job: clone repository and execute script."""
        logger.info(f"Starting job {self.name}")
        
        try:
            # Clone repository and checkout commit
            self.clone_repository()
            
            # Execute the script
            result = self.execute_script()
            
            logger.info(f"Job {self.name} finished with success={result.success}")
            return result
            
        except Exception as e:
            error_msg = f"Job {self.name} failed: {e}"
            logger.error(error_msg)
            return JobResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=error_msg
            )
    
    def cleanup(self) -> None:
        """Clean up the work directory."""
        if self.work_dir and self.work_dir.exists():
            logger.info(f"Cleaning up work directory {self.work_dir}")
            shutil.rmtree(self.work_dir)