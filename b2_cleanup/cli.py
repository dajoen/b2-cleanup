"""Command-line interface for B2 cleanup tool."""

import logging
import click
from .core import B2CleanupTool


@click.command()
@click.argument("bucket", required=False)
@click.option("--dry-run", is_flag=True, help="List only, don't delete anything")
@click.option("--key-id", help="B2 application key ID (overrides env vars)")
@click.option("--key", help="B2 application key (overrides env vars)")
@click.option("--non-interactive", is_flag=True, help="Disable interactive prompts")
def cli(bucket, dry_run, key_id, key, non_interactive):
    """Clean up unfinished B2 large file uploads in the specified bucket.
    
    If no bucket is specified, you'll be prompted to select one from your available buckets.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler("b2_cleanup.log")
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