# Job Scheduler

A Python-based job scheduler that clones repositories, checks out specific commits, and executes scripts. Built with modern Python tooling and designed for reliability and ease of use.

## Features

- **Repository Management**: Clone any Git repository and checkout specific commits
- **Script Execution**: Run arbitrary scripts in the cloned repository context
- **Parallel Execution**: Run multiple jobs concurrently with configurable worker limits
- **Configuration-Driven**: Define jobs using YAML or JSON configuration files
- **Environment Variables**: Set custom environment variables for each job
- **Timeout Control**: Configure execution timeouts to prevent hanging jobs
- **Cleanup Management**: Automatic cleanup of temporary directories
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Installation

```bash
# Install from source
pip install -e .

# Or install dependencies manually
pip install GitPython click pydantic pyyaml
```

## Quick Start

### 1. Create a Configuration File

```bash
# Create a sample configuration
job-scheduler create-config examples/my-jobs.yml
```

### 2. Run Jobs

```bash
# Run jobs from configuration file
job-scheduler run examples/my-jobs.yml

# Run jobs sequentially
job-scheduler run examples/my-jobs.yml --sequential

# Run with custom worker count
job-scheduler run examples/my-jobs.yml --max-workers 8
```

### 3. Run a Single Job

```bash
job-scheduler run-single \
  "my-job" \
  "https://github.com/octocat/Hello-World.git" \
  "master" \
  "echo 'Hello World!' && ls -la" \
  --timeout 300
```

## Configuration Format

### YAML Example

```yaml
max_workers: 4
cleanup_on_completion: true
parallel: true
jobs:
  - name: "hello-world"
    repo_url: "https://github.com/octocat/Hello-World.git"
    commit: "master"
    script: |
      echo "Hello from job scheduler!"
      ls -la
      git log --oneline -5
    work_dir: ""
    env_vars:
      JOB_NAME: "hello-world"
      CUSTOM_VAR: "value"
    timeout: 300
```

### JSON Example

```json
{
  "max_workers": 4,
  "cleanup_on_completion": true,
  "parallel": true,
  "jobs": [
    {
      "name": "simple-job",
      "repo_url": "https://github.com/octocat/Hello-World.git",
      "commit": "master",
      "script": "echo 'Hello World!' && date",
      "work_dir": "",
      "env_vars": {
        "JOB_NAME": "simple-job"
      },
      "timeout": 300
    }
  ]
}
```

## Command Line Interface

### Available Commands

- `run <config_file>` - Run jobs from configuration file
- `run-single <name> <repo_url> <commit> <script>` - Run a single job
- `create-config <output_file>` - Create sample configuration
- `validate <config_file>` - Validate configuration file

### Global Options

- `--verbose, -v` - Enable verbose logging
- `--help` - Show help message

### Run Command Options

- `--parallel/--sequential` - Run jobs in parallel or sequentially (default: parallel)
- `--max-workers, -w` - Maximum number of parallel workers (default: 4)
- `--no-cleanup` - Skip cleanup of work directories

### Run-Single Command Options

- `--work-dir, -d` - Custom work directory
- `--env, -e` - Environment variables (KEY=VALUE format, can be used multiple times)
- `--timeout, -t` - Timeout in seconds (default: 300)
- `--no-cleanup` - Skip cleanup of work directory

## Examples

See the `examples/` directory for sample configuration files:

- `examples/sample-jobs.yml` - Multiple jobs with different configurations
- `examples/simple-job.json` - Single job in JSON format

## Architecture

The job scheduler consists of several key components:

- **Job**: Represents a single job with repository, commit, and script information
- **Scheduler**: Manages multiple jobs and handles parallel execution
- **Config**: Configuration loading and validation using Pydantic
- **CLI**: Command-line interface built with Click

## Error Handling

The scheduler provides comprehensive error handling:

- Repository cloning failures
- Git checkout failures  
- Script execution failures
- Timeout handling
- Network connectivity issues

All errors are logged with detailed information for debugging.

## License

MIT License - see LICENSE file for details.