"""Scheduler class for managing and executing multiple jobs."""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .job import Job, JobResult

logger = logging.getLogger(__name__)


class Scheduler:
    """Manages and executes multiple jobs."""
    
    def __init__(self, max_workers: int = 4, cleanup_on_completion: bool = True):
        """Initialize the scheduler.
        
        Args:
            max_workers: Maximum number of concurrent jobs
            cleanup_on_completion: Whether to cleanup job directories after completion
        """
        self.max_workers = max_workers
        self.cleanup_on_completion = cleanup_on_completion
        self.jobs: List[Job] = []
        self.results: Dict[str, JobResult] = {}
    
    def add_job(self, job: Job) -> None:
        """Add a job to the scheduler."""
        self.jobs.append(job)
        logger.info(f"Added job {job.name} to scheduler")
    
    def add_jobs_from_config(self, config: Dict[str, Any]) -> None:
        """Add jobs from a configuration dictionary."""
        jobs_config = config.get('jobs', [])
        
        for job_config in jobs_config:
            job = Job(
                name=job_config['name'],
                repo_url=job_config['repo_url'],
                commit=job_config['commit'],
                script=job_config['script'],
                work_dir=Path(job_config.get('work_dir', '')) if job_config.get('work_dir') else None,
                env_vars=job_config.get('env_vars', {}),
                timeout=job_config.get('timeout', 300)
            )
            self.add_job(job)
    
    def run_job(self, job: Job) -> tuple[str, JobResult]:
        """Run a single job and return the result."""
        try:
            result = job.run()
            return job.name, result
        finally:
            if self.cleanup_on_completion:
                job.cleanup()
    
    def run_jobs_sequential(self) -> Dict[str, JobResult]:
        """Run all jobs sequentially."""
        logger.info(f"Running {len(self.jobs)} jobs sequentially")
        
        results = {}
        for job in self.jobs:
            logger.info(f"Starting job {job.name}")
            name, result = self.run_job(job)
            results[name] = result
            
            if result.success:
                logger.info(f"Job {name} completed successfully")
            else:
                logger.error(f"Job {name} failed: {result.error_message or 'Script failed'}")
        
        self.results.update(results)
        return results
    
    def run_jobs_parallel(self) -> Dict[str, JobResult]:
        """Run all jobs in parallel using ThreadPoolExecutor."""
        logger.info(f"Running {len(self.jobs)} jobs in parallel (max_workers={self.max_workers})")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_job = {executor.submit(self.run_job, job): job for job in self.jobs}
            
            # Process completed jobs
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    name, result = future.result()
                    results[name] = result
                    
                    if result.success:
                        logger.info(f"Job {name} completed successfully")
                    else:
                        logger.error(f"Job {name} failed: {result.error_message or 'Script failed'}")
                        
                except Exception as e:
                    logger.error(f"Job {job.name} raised an exception: {e}")
                    results[job.name] = JobResult(
                        success=False,
                        exit_code=-1,
                        stdout="",
                        stderr="",
                        error_message=str(e)
                    )
        
        self.results.update(results)
        return results
    
    def run_jobs(self, parallel: bool = True) -> Dict[str, JobResult]:
        """Run all jobs either in parallel or sequentially."""
        if not self.jobs:
            logger.warning("No jobs to run")
            return {}
        
        if parallel:
            return self.run_jobs_parallel()
        else:
            return self.run_jobs_sequential()
    
    def get_results(self) -> Dict[str, JobResult]:
        """Get the results of all executed jobs."""
        return self.results.copy()
    
    def get_successful_jobs(self) -> List[str]:
        """Get the names of all successful jobs."""
        return [name for name, result in self.results.items() if result.success]
    
    def get_failed_jobs(self) -> List[str]:
        """Get the names of all failed jobs."""
        return [name for name, result in self.results.items() if not result.success]
    
    def print_summary(self) -> None:
        """Print a summary of job execution results."""
        if not self.results:
            print("No jobs have been executed yet.")
            return
        
        successful = self.get_successful_jobs()
        failed = self.get_failed_jobs()
        
        print(f"\n=== Job Execution Summary ===")
        print(f"Total jobs: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            print(f"\nSuccessful jobs:")
            for job_name in successful:
                print(f"  ✓ {job_name}")
        
        if failed:
            print(f"\nFailed jobs:")
            for job_name in failed:
                result = self.results[job_name]
                error_msg = result.error_message or f"Exit code: {result.exit_code}"
                print(f"  ✗ {job_name}: {error_msg}")
        
        print()
    
    def clear_jobs(self) -> None:
        """Clear all jobs and results."""
        self.jobs.clear()
        self.results.clear()
        logger.info("Cleared all jobs and results")