"""Command-line interface for B2 cleanup tool."""

import os
import logging
import click
from datetime import datetime
from .core import B2CleanupTool

# Define a default log file path
log_file = os.path.join(os.getcwd(), f"b2-cleanup-{datetime.now().strftime('%Y-%m-%d')}.log")

@click.command()
@click.argument("bucket", required=False)
@click.option("--dry-run", is_flag=True, help="List only, don't delete anything")
@click.option("--key-id", help="B2 application key ID (overrides env vars)")
@click.option("--key", help="B2 application key (overrides env vars)")
@click.option("--non-interactive", is_flag=True, help="Disable interactive prompts")
@click.option("--log-file", help="Path to log file", default=None)
def cli(bucket, dry_run, key_id, key, non_interactive, log_file=None):
    """Clean up unfinished B2 large file uploads in the specified bucket.
    
    If no bucket is specified, you'll be prompted to select one from your available buckets.
    """
    # Use the global log_file if not specified via CLI
    if log_file is None:
        log_file = globals()['log_file']
        
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(stream_handler)

    tool = B2CleanupTool(
        dry_run=dry_run,
        override_key_id=key_id,
        override_key=key,
    )
    
    tool.cleanup_unfinished_uploads(bucket, interactive=not non_interactive)


if __name__ == "__main__":
    cli()  # pragma: no cover