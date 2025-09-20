"""Basic tests for the job scheduler."""

import tempfile
import shutil
from pathlib import Path
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / '../src'))

from job_scheduler.job import Job, JobResult
from job_scheduler.scheduler import Scheduler
from job_scheduler.config import load_config, save_config, create_sample_config


class TestJob:
    """Test the Job class."""
    
    def test_job_creation(self):
        """Test job creation with basic parameters."""
        job = Job(
            name="test-job",
            repo_url="https://github.com/octocat/Hello-World.git",
            commit="master",
            script="echo 'test'"
        )
        
        assert job.name == "test-job"
        assert job.repo_url == "https://github.com/octocat/Hello-World.git"
        assert job.commit == "master"
        assert job.script == "echo 'test'"
        assert job.timeout == 300
        assert job.env_vars == {}
        assert job.work_dir is not None
    
    def test_job_with_custom_work_dir(self):
        """Test job creation with custom work directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            job = Job(
                name="test-job",
                repo_url="https://github.com/octocat/Hello-World.git",
                commit="master",
                script="echo 'test'",
                work_dir=Path(temp_dir) / "custom"
            )
            
            assert str(job.work_dir).endswith("custom")
    
    def test_simple_script_execution(self):
        """Test simple script execution without repository cloning."""
        job = Job(
            name="simple-test",
            repo_url="https://github.com/octocat/Hello-World.git",
            commit="master",
            script="echo 'Hello World'",
            timeout=30
        )
        
        # Just test script execution without cloning
        result = job.execute_script()
        
        assert result.success is True
        assert result.exit_code == 0
        assert "Hello World" in result.stdout
        
        job.cleanup()


class TestScheduler:
    """Test the Scheduler class."""
    
    def test_scheduler_creation(self):
        """Test scheduler creation."""
        scheduler = Scheduler(max_workers=2, cleanup_on_completion=True)
        
        assert scheduler.max_workers == 2
        assert scheduler.cleanup_on_completion is True
        assert len(scheduler.jobs) == 0
        assert len(scheduler.results) == 0
    
    def test_add_job(self):
        """Test adding a job to the scheduler."""
        scheduler = Scheduler()
        job = Job(
            name="test-job",
            repo_url="https://github.com/octocat/Hello-World.git",
            commit="master",
            script="echo 'test'"
        )
        
        scheduler.add_job(job)
        
        assert len(scheduler.jobs) == 1
        assert scheduler.jobs[0].name == "test-job"
    
    def test_add_jobs_from_config(self):
        """Test adding jobs from configuration."""
        scheduler = Scheduler()
        config = create_sample_config()
        
        scheduler.add_jobs_from_config(config)
        
        assert len(scheduler.jobs) == 1
        assert scheduler.jobs[0].name == "example-job"


class TestConfig:
    """Test configuration handling."""
    
    def test_create_sample_config(self):
        """Test creating sample configuration."""
        config = create_sample_config()
        
        assert "max_workers" in config
        assert "cleanup_on_completion" in config
        assert "parallel" in config
        assert "jobs" in config
        assert len(config["jobs"]) == 1
        assert config["jobs"][0]["name"] == "example-job"
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        config = create_sample_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config_path = f.name
        
        try:
            # Save config
            save_config(config, config_path)
            
            # Load config
            loaded_config = load_config(config_path)
            
            # Verify
            assert loaded_config["max_workers"] == config["max_workers"]
            assert loaded_config["cleanup_on_completion"] == config["cleanup_on_completion"]
            assert len(loaded_config["jobs"]) == len(config["jobs"])
            
        finally:
            Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    # Run a simple test
    print("Running basic tests...")
    
    # Test Job creation
    job = Job(
        name="test",
        repo_url="https://github.com/octocat/Hello-World.git", 
        commit="master",
        script="echo 'test'"
    )
    print("✓ Job creation test passed")
    
    # Test Scheduler creation
    scheduler = Scheduler()
    scheduler.add_job(job)
    print("✓ Scheduler test passed")
    
    # Test Config
    config = create_sample_config()
    print("✓ Config test passed")
    
    print("All basic tests passed!")