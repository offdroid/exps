"""Configuration handling for job scheduler."""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Union, List
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class JobConfig(BaseModel):
    """Configuration for a single job."""
    name: str
    repo_url: str
    commit: str
    script: str
    work_dir: str = ""
    env_vars: Dict[str, str] = Field(default_factory=dict)
    timeout: int = 300
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Job name cannot be empty')
        return v.strip()
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        if not v or not v.strip():
            raise ValueError('Repository URL cannot be empty')
        return v.strip()
    
    @validator('commit')
    def validate_commit(cls, v):
        if not v or not v.strip():
            raise ValueError('Commit cannot be empty')
        return v.strip()
    
    @validator('script')
    def validate_script(cls, v):
        if not v or not v.strip():
            raise ValueError('Script cannot be empty')
        return v.strip()


class SchedulerConfig(BaseModel):
    """Configuration for the scheduler."""
    max_workers: int = 4
    cleanup_on_completion: bool = True
    parallel: bool = True
    jobs: List[JobConfig] = Field(default_factory=list)
    
    @validator('max_workers')
    def validate_max_workers(cls, v):
        if v < 1:
            raise ValueError('max_workers must be at least 1')
        return v


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from a YAML or JSON file."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    logger.info(f"Loading configuration from {config_path}")
    
    with open(config_path, 'r') as f:
        if config_path.suffix.lower() in ['.yml', '.yaml']:
            config_data = yaml.safe_load(f)
        elif config_path.suffix.lower() == '.json':
            config_data = json.load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
    
    # Validate the configuration
    try:
        config = SchedulerConfig(**config_data)
        logger.info(f"Configuration loaded successfully with {len(config.jobs)} jobs")
        return config.dict()
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")


def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> None:
    """Save configuration to a YAML or JSON file."""
    config_path = Path(config_path)
    
    # Validate the configuration before saving
    SchedulerConfig(**config)
    
    logger.info(f"Saving configuration to {config_path}")
    
    with open(config_path, 'w') as f:
        if config_path.suffix.lower() in ['.yml', '.yaml']:
            yaml.safe_dump(config, f, default_flow_style=False)
        elif config_path.suffix.lower() == '.json':
            json.dump(config, f, indent=2)
        else:
            raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
    
    logger.info(f"Configuration saved successfully")


def create_sample_config() -> Dict[str, Any]:
    """Create a sample configuration dictionary."""
    return {
        "max_workers": 4,
        "cleanup_on_completion": True,
        "parallel": True,
        "jobs": [
            {
                "name": "example-job",
                "repo_url": "https://github.com/example/repo.git",
                "commit": "main",
                "script": "echo 'Hello from job scheduler!' && ls -la",
                "work_dir": "",
                "env_vars": {
                    "JOB_NAME": "example-job",
                    "CUSTOM_VAR": "custom_value"
                },
                "timeout": 300
            }
        ]
    }