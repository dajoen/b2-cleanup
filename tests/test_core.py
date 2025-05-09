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

    @patch("b2_cleanup.core.B2Api")
    def test_cleanup_nonexistent_bucket(self, mock_b2api):
        """Test handling of a non-existent bucket."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        
        # Simulate bucket not found
        mock_api.get_bucket_by_name.side_effect = Exception("Bucket not found")
        
        tool = B2CleanupTool(override_key_id="test_id", override_key="test_key")
        
        with pytest.raises(RuntimeError) as excinfo:
            tool.cleanup_unfinished_uploads("nonexistent-bucket")
        
        assert "Cannot access bucket" in str(excinfo.value)
        mock_api.get_bucket_by_name.assert_called_once_with("nonexistent-bucket")

    @patch("b2_cleanup.core.B2Api")
    def test_cleanup_suggests_similar_bucket_names(self, mock_b2api):
        """Test that suggestions are provided for similar bucket names."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        
        # Mock available buckets
        mock_bucket1 = MagicMock()
        mock_bucket1.name = "my-real-bucket"
        mock_bucket2 = MagicMock()
        mock_bucket2.name = "my-other-bucket"
        mock_api.list_buckets.return_value = [mock_bucket1, mock_bucket2]
        
        # Simulate bucket not found
        mock_api.get_bucket_by_name.side_effect = Exception("Bucket not found")
        
        tool = B2CleanupTool(override_key_id="test_id", override_key="test_key")
        
        # Check that when non-interactive, we get a simple error without suggestions
        with pytest.raises(RuntimeError) as excinfo:
            tool.cleanup_unfinished_uploads("my-reel-bucket", interactive=False)
        
        assert "Cannot access bucket 'my-reel-bucket'" in str(excinfo.value)
        assert "Did you mean" not in str(excinfo.value)  # Should not have suggestion
        
        # Reset the mock to test interactive mode
        mock_api.get_bucket_by_name.reset_mock()
        mock_api.get_bucket_by_name.side_effect = Exception("Bucket not found")
        
        # For testing interactive mode, we need to patch input() function
        with patch('builtins.input', return_value='n'):  # Simulate user answering "no"
            with pytest.raises(RuntimeError) as excinfo:
                tool.cleanup_unfinished_uploads("my-reel-bucket", interactive=True)
            
            # Should include suggestion in error message when interactive=True
            # Check for the presence of both buckets in the suggestion
            error_msg = str(excinfo.value)
            assert "Did you mean one of these" in error_msg
            assert "my-real-bucket" in error_msg
            assert "my-other-bucket" in error_msg

    @patch("b2_cleanup.core.B2Api")
    def test_interactive_single_suggestion_accepted(self, mock_b2api):
        """Test accepting a single bucket name suggestion."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        
        # Mock a single bucket
        mock_bucket = MagicMock()
        mock_bucket.name = "my-real-bucket"
        mock_api.list_buckets.return_value = [mock_bucket]
        
        # First call fails, second call succeeds (after correction)
        mock_api.get_bucket_by_name.side_effect = [
            Exception("Bucket not found"),  # First call (with typo)
            MagicMock()  # Second call (with corrected name)
        ]
        
        # Mock the user accepting the suggestion
        with patch('builtins.input', return_value='y'):
            tool = B2CleanupTool(override_key_id="test_id", override_key="test_key")
            tool.cleanup_unfinished_uploads("my-reel-bucket", interactive=True)
        
        # Should have made 2 calls - first with the typo, then with the corrected name
        assert mock_api.get_bucket_by_name.call_count == 2
        mock_api.get_bucket_by_name.assert_has_calls([
            call("my-reel-bucket"),
            call("my-real-bucket")
        ])

    @patch("b2_cleanup.core.B2Api")
    def test_interactive_multiple_suggestion_selection(self, mock_b2api):
        """Test selecting from multiple bucket name suggestions."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        
        # Mock multiple buckets
        mock_bucket1 = MagicMock()
        mock_bucket1.name = "my-real-bucket"
        mock_bucket2 = MagicMock()
        mock_bucket2.name = "my-other-bucket"
        mock_api.list_buckets.return_value = [mock_bucket1, mock_bucket2]
        
        # First call fails, second call succeeds (after correction)
        mock_api.get_bucket_by_name.side_effect = [
            Exception("Bucket not found"),  # First call (with typo)
            MagicMock()  # Second call (with selected name)
        ]
        
        # Mock the user selecting option 2
        with patch('builtins.input', return_value='2'):
            tool = B2CleanupTool(override_key_id="test_id", override_key="test_key")
            tool.cleanup_unfinished_uploads("my-reel-bucket", interactive=True)
        
        # Should have made 2 calls - first with the typo, then with the selected name
        assert mock_api.get_bucket_by_name.call_count == 2
        mock_api.get_bucket_by_name.assert_has_calls([
            call("my-reel-bucket"),
            call("my-other-bucket")
        ])

    @patch("b2_cleanup.core.B2Api")
    def test_interactive_invalid_selection(self, mock_b2api):
        """Test invalid selection from bucket suggestions."""
        mock_api = MagicMock()
        mock_b2api.return_value = mock_api
        
        # Mock buckets
        mock_bucket1 = MagicMock()
        mock_bucket1.name = "my-real-bucket"
        mock_bucket2 = MagicMock()
        mock_bucket2.name = "my-other-bucket"
        mock_api.list_buckets.return_value = [mock_bucket1, mock_bucket2]
        
        # Bucket not found
        mock_api.get_bucket_by_name.side_effect = Exception("Bucket not found")
        
        # Test with invalid selection (out of range or non-numeric)
        with patch('builtins.input', return_value='99'):
            tool = B2CleanupTool(override_key_id="test_id", override_key="test_key")
            with pytest.raises(RuntimeError) as excinfo:
                tool.cleanup_unfinished_uploads("my-reel-bucket", interactive=True)
        
        assert "Operation canceled" in str(excinfo.value)