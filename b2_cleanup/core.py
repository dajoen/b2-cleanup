"""Core functionality for B2 cleanup tool."""

import os
import json
import subprocess
import logging
from b2sdk.v2 import InMemoryAccountInfo, B2Api


class B2CleanupTool:
    """Tool to clean up unfinished large file uploads in B2 buckets."""

    def __init__(
        self,
        dry_run: bool = False,
        override_key_id: str = None,
        override_key: str = None,
    ):
        """Initialize the B2 cleanup tool.

        Args:
            dry_run: If True, only list uploads but don't delete them
            override_key_id: Optional B2 key ID to override env/config
            override_key: Optional B2 application key to override env/config
        """
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
            try:
                result = subprocess.run(
                    ["b2", "account", "get"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except FileNotFoundError:
                self.logger.error("❌ Command 'b2' not found. Please install the B2 CLI or provide credentials.")
                raise RuntimeError("B2 CLI not found. Please install it or provide credentials manually.")
                
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
        """Find and clean up unfinished uploads in the specified bucket.

        Args:
            bucket_name: Name of the B2 bucket to clean up
        """
        bucket = self.api.get_bucket_by_name(bucket_name)
        unfinished = list(bucket.list_unfinished_large_files())
        if not unfinished:
            self.logger.info("✅ No unfinished large files found.")
            return

        self.logger.info("🗃️ Found %d unfinished uploads", len(unfinished))
        for file_version in unfinished:
            # Use the correct attribute names for UnfinishedLargeFile objects
            file_id = file_version.file_id
            file_name = file_version.file_name
            if self.dry_run:
                self.logger.info(f"💡 Dry run: would cancel {file_id} ({file_name})")
            else:
                self.logger.info(f"🗑️ Cancelling {file_id} ({file_name})")
                self.api.cancel_large_file(file_id)