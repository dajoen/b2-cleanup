"""Command-line interface for B2 cleanup tool."""

import logging
import click
from .core import B2CleanupTool


@click.command()
@click.argument("bucket")
@click.option(
    "--dry-run", is_flag=True, help="Only list unfinished uploads, do not cancel."
)
@click.option("--log-file", default="b2_cleanup.log", help="Path to log file.")
@click.option("--key-id", help="Backblaze B2 applicationKeyId to override env/config.")
@click.option("--key", help="Backblaze B2 applicationKey to override env/config.")
def cli(bucket, dry_run, log_file, key_id, key):
    """Clean up unfinished large file uploads in BUCKET."""
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

    tool = B2CleanupTool(dry_run=dry_run, override_key_id=key_id, override_key=key)
    tool.cleanup_unfinished_uploads(bucket)


if __name__ == "__main__":
    cli()  # pragma: no cover