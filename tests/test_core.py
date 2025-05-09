"""Tests for the core B2 cleanup functionality."""

import os
import json
import subprocess
from unittest.mock import patch, MagicMock, call

import pytest
from b2sdk.v2 import B2Api

from b2_cleanup.core import B2CleanupTool


class TestB2CleanupTool:
    """Test the B2CleanupTool class."""

    @patch("b2_cleanup.core.B2Api")
    def test_init_with_cli_credentials(self, mock_b2api):
        """Test initialization with CLI credentials."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api

        tool = B2CleanupTool(
            dry_run=True, 
            override_key_id="test_key_id", 
            override_key="test_key"
        )

        mock_api.authorize_account.assert_called_once_with(
            "production", "test_key_id", "test_key"
        )
        assert tool.dry_run is True

    @patch("b2_cleanup.core.B2Api")
    @patch.dict("os.environ", {"B2_APPLICATION_KEY_ID": "env_key_id", "B2_APPLICATION_KEY": "env_key"})
    def test_init_with_env_credentials(self, mock_b2api):
        """Test initialization with environment variable credentials."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api

        tool = B2CleanupTool()

        mock_api.authorize_account.assert_called_once_with(
            "production", "env_key_id", "env_key"
        )

    @patch("b2_cleanup.core.B2Api")
    @patch("b2_cleanup.core.subprocess.run")
    def test_init_with_b2_cli(self, mock_run, mock_b2api):
        """Test initialization using B2 CLI credentials."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        mock_run.return_value.stdout = json.dumps({
            "applicationKeyId": "cli_key_id",
            "applicationKey": "cli_key"
        })

        tool = B2CleanupTool()

        mock_run.assert_called_once_with(
            ["b2", "account", "get"],
            check=True,
            capture_output=True,
            text=True
        )
        mock_api.authorize_account.assert_called_once_with(
            "production", "cli_key_id", "cli_key"
        )

    @patch("b2_cleanup.core.B2Api")
    @patch("b2_cleanup.core.subprocess.run")
    def test_b2_cli_not_found(self, mock_run, mock_b2api):
        """Test handling when B2 CLI is not installed."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'b2'")

        with pytest.raises(RuntimeError) as excinfo:
            B2CleanupTool()

        assert "B2 CLI not found" in str(excinfo.value)

    @patch("b2_cleanup.core.B2Api")
    def test_cleanup_unfinished_uploads_empty(self, mock_b2api):
        """Test cleanup when no unfinished uploads exist."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        
        mock_bucket = MagicMock()
        mock_bucket.list_unfinished_large_files.return_value = []
        mock_api.get_bucket_by_name.return_value = mock_bucket

        tool = B2CleanupTool(override_key_id="test_id", override_key="test_key")
        tool.cleanup_unfinished_uploads("test-bucket")

        mock_api.get_bucket_by_name.assert_called_once_with("test-bucket")
        mock_bucket.list_unfinished_large_files.assert_called_once()
        # No calls to cancel_large_file should happen
        mock_api.cancel_large_file.assert_not_called()

    @patch("b2_cleanup.core.B2Api")
    def test_cleanup_unfinished_uploads_dry_run(self, mock_b2api):
        """Test cleanup in dry run mode."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        
        # Create mock unfinished files
        mock_file1 = MagicMock()
        mock_file1.file_id = "file1_id"
        mock_file1.file_name = "file1.txt"
        
        mock_file2 = MagicMock()
        mock_file2.file_id = "file2_id"
        mock_file2.file_name = "file2.txt"
        
        mock_bucket = MagicMock()
        mock_bucket.list_unfinished_large_files.return_value = [mock_file1, mock_file2]
        mock_api.get_bucket_by_name.return_value = mock_bucket

        # Initialize with dry_run=True
        tool = B2CleanupTool(
            dry_run=True, 
            override_key_id="test_id", 
            override_key="test_key"
        )
        tool.cleanup_unfinished_uploads("test-bucket")

        mock_api.get_bucket_by_name.assert_called_once_with("test-bucket")
        mock_bucket.list_unfinished_large_files.assert_called_once()
        # No calls to cancel_large_file should happen in dry run mode
        mock_api.cancel_large_file.assert_not_called()

    @patch("b2_cleanup.core.B2Api")
    def test_cleanup_unfinished_uploads_delete(self, mock_b2api):
        """Test cleanup with actual deletion."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        
        # Create mock unfinished files
        mock_file1 = MagicMock()
        mock_file1.file_id = "file1_id"
        mock_file1.file_name = "file1.txt"
        
        mock_file2 = MagicMock()
        mock_file2.file_id = "file2_id"
        mock_file2.file_name = "file2.txt"
        
        mock_bucket = MagicMock()
        mock_bucket.list_unfinished_large_files.return_value = [mock_file1, mock_file2]
        mock_api.get_bucket_by_name.return_value = mock_bucket

        # Initialize with dry_run=False (default)
        tool = B2CleanupTool(override_key_id="test_id", override_key="test_key")
        tool.cleanup_unfinished_uploads("test-bucket")

        mock_api.get_bucket_by_name.assert_called_once_with("test-bucket")
        mock_bucket.list_unfinished_large_files.assert_called_once()
        
        # Verify cancel_large_file is called for each file
        assert mock_api.cancel_large_file.call_count == 2
        mock_api.cancel_large_file.assert_has_calls([
            call("file1_id"),
            call("file2_id")
        ])