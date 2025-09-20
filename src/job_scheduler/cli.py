"""Command line interface for the job scheduler."""

import click
import logging
import sys
from pathlib import Path
from typing import Optional

from .scheduler import Scheduler
from .job import Job
from .config import load_config, save_config, create_sample_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Job Scheduler - Clone repositories and execute jobs."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--parallel/--sequential', default=True, help='Run jobs in parallel or sequential')
@click.option('--max-workers', '-w', default=4, help='Maximum number of parallel workers')
@click.option('--no-cleanup', is_flag=True, help='Skip cleanup of work directories')
def run(config_file: str, parallel: bool, max_workers: int, no_cleanup: bool):
    """Run jobs from a configuration file."""
    try:
        # Load configuration
        config = load_config(config_file)
        
        # Override config with command line options
        config['parallel'] = parallel
        config['max_workers'] = max_workers
        config['cleanup_on_completion'] = not no_cleanup
        
        # Create scheduler
        scheduler = Scheduler(
            max_workers=config['max_workers'],
            cleanup_on_completion=config['cleanup_on_completion']
        )
        
        # Add jobs from config
        scheduler.add_jobs_from_config(config)
        
        if not scheduler.jobs:
            click.echo("No jobs found in configuration file.", err=True)
            sys.exit(1)
        
        click.echo(f"Starting {len(scheduler.jobs)} jobs...")
        
        # Run jobs
        results = scheduler.run_jobs(parallel=config['parallel'])
        
        # Print summary
        scheduler.print_summary()
        
        # Exit with error code if any job failed
        failed_jobs = scheduler.get_failed_jobs()
        if failed_jobs:
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command('run-single')
@click.argument('name')
@click.argument('repo_url')
@click.argument('commit')
@click.argument('script')
@click.option('--work-dir', '-d', help='Work directory for the job')
@click.option('--env', '-e', multiple=True, help='Environment variables (KEY=VALUE)')
@click.option('--timeout', '-t', default=300, help='Timeout in seconds')
@click.option('--no-cleanup', is_flag=True, help='Skip cleanup of work directory')
def run_single(name: str, repo_url: str, commit: str, script: str, 
               work_dir: Optional[str], env: tuple, timeout: int, no_cleanup: bool):
    """Run a single job directly from command line."""
    try:
        # Parse environment variables
        env_vars = {}
        for env_var in env:
            if '=' not in env_var:
                click.echo(f"Invalid environment variable format: {env_var}", err=True)
                sys.exit(1)
            key, value = env_var.split('=', 1)
            env_vars[key] = value
        
        # Create job
        job = Job(
            name=name,
            repo_url=repo_url,
            commit=commit,
            script=script,
            work_dir=Path(work_dir) if work_dir else None,
            env_vars=env_vars,
            timeout=timeout
        )
        
        click.echo(f"Running job '{name}'...")
        
        # Run job
        result = job.run()
        
        # Print result
        if result.success:
            click.echo(f"Job '{name}' completed successfully!")
            if result.stdout:
                click.echo("STDOUT:")
                click.echo(result.stdout)
        else:
            click.echo(f"Job '{name}' failed!", err=True)
            if result.error_message:
                click.echo(f"Error: {result.error_message}", err=True)
            if result.stderr:
                click.echo("STDERR:", err=True)
                click.echo(result.stderr, err=True)
            sys.exit(1)
            
        # Cleanup
        if not no_cleanup:
            job.cleanup()
        else:
            click.echo(f"Work directory preserved at: {job.work_dir}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command('create-config')
@click.argument('output_file', type=click.Path())
@click.option('--format', 'config_format', type=click.Choice(['yaml', 'json']), 
              default='yaml', help='Configuration file format')
def create_config(output_file: str, config_format: str):
    """Create a sample configuration file."""
    try:
        output_path = Path(output_file)
        
        # Ensure the file has the right extension
        if config_format == 'yaml' and not output_path.suffix.lower() in ['.yml', '.yaml']:
            output_path = output_path.with_suffix('.yml')
        elif config_format == 'json' and not output_path.suffix.lower() == '.json':
            output_path = output_path.with_suffix('.json')
        
        # Create sample config
        config = create_sample_config()
        
        # Save config
        save_config(config, output_path)
        
        click.echo(f"Sample configuration created at: {output_path}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('config_file', type=click.Path(exists=True))
def validate(config_file: str):
    """Validate a configuration file."""
    try:
        config = load_config(config_file)
        click.echo(f"Configuration file is valid!")
        click.echo(f"Found {len(config['jobs'])} job(s)")
        
        for job in config['jobs']:
            click.echo(f"  - {job['name']}: {job['repo_url']} @ {job['commit']}")
            
    except Exception as e:
        click.echo(f"Configuration file is invalid: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()