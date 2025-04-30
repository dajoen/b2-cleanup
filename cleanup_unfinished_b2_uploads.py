import os
import json
import subprocess
import logging
import click
from b2sdk.v2 import InMemoryAccountInfo, B2Api


class B2CleanupTool:
    def __init__(
        self,
        dry_run: bool = False,
        override_key_id: str = None,
        override_key: str = None,
    ):
        self.dry_run = dry_run
        self.logger = logging.getLogger("B2Cleanup")
        self.api = self._authorize(override_key_id, override_key)

    def _authorize(self, override_key_id=None, override_key=None):
        info = InMemoryAccountInfo()
        api = B2Api(info)

        if override_key_id and override_key:
            self.logger.info("🔐 Using credentials from CLI override.")
            api.authorize_account("production", override_key_id, override_key)
            return api

        key_id = os.getenv("B2_APPLICATION_KEY_ID")
        app_key = os.getenv("B2_APPLICATION_KEY")

        if key_id and app_key:
            self.logger.info("🔐 Using credentials from environment variables.")
            api.authorize_account("production", key_id, app_key)
            return api

        try:
            self.logger.info("🔍 Trying to load credentials via `b2 account get`...")
            result = subprocess.run(
                ["b2", "account", "get"],
                check=True,
                capture_output=True,
                text=True,
            )
            creds = json.loads(result.stdout)
            key_id = creds["applicationKeyId"]
            app_key = creds["applicationKey"]
            api.authorize_account("production", key_id, app_key)
            self.logger.info("✅ Authorized with B2 CLI credentials.")
            return api

        except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as e:
            self.logger.error(
                "❌ Failed to get B2 credentials from CLI or environment: %s", e
            )
            raise RuntimeError("Could not authorize with Backblaze B2.")

    def cleanup_unfinished_uploads(self, bucket_name: str):
        bucket = self.api.get_bucket_by_name(bucket_name)
        unfinished = list(bucket.list_unfinished_large_files())
        if not unfinished:
            self.logger.info("✅ No unfinished large files found.")
            return

        self.logger.info("🗃️ Found %d unfinished uploads", len(unfinished))
        for file_version in unfinished:
            file_id = file_version.id_
            file_name = file_version.file_name
            if self.dry_run:
                self.logger.info(f"💡 Dry run: would cancel {file_id} ({file_name})")
            else:
                self.logger.info(f"🗑️ Cancelling {file_id} ({file_name})")
                self.api.cancel_large_file(file_id)


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
    cli()
