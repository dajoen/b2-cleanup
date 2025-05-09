"""Core functionality for B2 cleanup tool."""

import os
import json
import subprocess
import logging
import difflib  # Add this import at the top
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
        self.available_buckets = self._fetch_available_buckets()

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

    def _fetch_available_buckets(self):
        """Fetch a list of available bucket names.
        
        Returns:
            A list of bucket names the user has access to.
        """
        try:
            self.logger.info("🔍 Fetching available buckets...")
            buckets = self.api.list_buckets()
            bucket_names = [b.name for b in buckets]
            self.logger.info(f"✅ Found {len(bucket_names)} available buckets")
            return bucket_names
        except Exception as e:
            self.logger.warning(f"⚠️ Could not fetch bucket list: {e}")
            return []

    def cleanup_unfinished_uploads(self, bucket_name: str, interactive: bool = True):
        """Find and clean up unfinished uploads in the specified bucket.

        Args:
            bucket_name: Name of the B2 bucket to clean up
            interactive: If True, allow interactive correction of bucket names
        """
        try:
            bucket = self.api.get_bucket_by_name(bucket_name)
        except Exception as e:
            # Generate suggestions from pre-fetched bucket list
            suggestion_msg = ""
            
            # Only generate suggestions in interactive mode
            if interactive and self.available_buckets:
                # Find close matches using difflib
                close_matches = difflib.get_close_matches(bucket_name, self.available_buckets, n=3, cutoff=0.6)
                
                if close_matches:
                    if len(close_matches) == 1:
                        suggestion_msg = f" Did you mean '{close_matches[0]}'?"
                        # Interactive correction
                        response = input(f"Use '{close_matches[0]}' instead? [y/N]: ").strip().lower()
                        if response == 'y' or response == 'yes':
                            self.logger.info(f"✅ Using bucket '{close_matches[0]}' instead")
                            return self.cleanup_unfinished_uploads(close_matches[0], interactive=False)
                    else:
                        suggestions = "', '".join(close_matches)
                        suggestion_msg = f" Did you mean one of these: '{suggestions}'?"
                        # Interactive multi-choice
                        self.logger.warning(f"⚠️ Bucket '{bucket_name}' not found. Did you mean one of these?")
                        for i, match in enumerate(close_matches, 1):
                            print(f"{i}. {match}")
                        
                        response = input("Enter number to use, or any other key to cancel: ").strip()
                        try:
                            idx = int(response) - 1
                            if 0 <= idx < len(close_matches):
                                suggested = close_matches[idx]
                                self.logger.info(f"✅ Using bucket '{suggested}' instead")
                                return self.cleanup_unfinished_uploads(suggested, interactive=False)
                        except ValueError:
                            pass  # Non-numeric input, just fall through to error
            
            # Show different messages depending on interactive mode
            if interactive:
                self.logger.error(f"❌ Bucket '{bucket_name}' not found or not accessible: {e}{suggestion_msg}")
                raise RuntimeError(f"Cannot access bucket '{bucket_name}'.{suggestion_msg} Please check the name and your permissions.")
            else:
                # Simple error without suggestions in non-interactive mode
                self.logger.error(f"❌ Bucket '{bucket_name}' not found or not accessible: {e}")
                raise RuntimeError(f"Cannot access bucket '{bucket_name}'. Please check the name and your permissions.")

        unfinished = list(bucket.list_unfinished_large_files())
        if not unfinished:
            self.logger.info("✅ No unfinished large files found.")
            return

        self.logger.info("🗃️ Found %d unfinished uploads", len(unfinished))
        for file_version in unfinished:
            file_id = file_version.file_id
            file_name = file_version.file_name
            if self.dry_run:
                self.logger.info(f"💡 Dry run: would cancel {file_id} ({file_name})")
            else:
                self.logger.info(f"🗑️ Cancelling {file_id} ({file_name})")
                self.api.cancel_large_file(file_id)