"""Tests for the CLI interface."""

from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from b2_cleanup.cli import cli


class TestCLI:
    """Test the CLI interface."""

    @patch("b2_cleanup.cli.logging")
    @patch("b2_cleanup.cli.B2CleanupTool")
    def test_cli_basic(self, mock_tool_class, mock_logging):
        """Test basic CLI functionality."""
        mock_tool = MagicMock()
        mock_tool_class.return_value = mock_tool

        runner = CliRunner()
        # Use a temporary log file path in tests
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["test-bucket", "--log-file", "test.log"])

        assert result.exit_code == 0
        mock_tool_class.assert_called_once_with(
            dry_run=False, override_key_id=None, override_key=None
        )
        mock_tool.cleanup_unfinished_uploads.assert_called_once_with(
            "test-bucket", interactive=True
        )

    @patch("b2_cleanup.cli.B2CleanupTool")
    def test_cli_dry_run(self, mock_tool_class):
        """Test CLI with dry run flag."""
        mock_tool = MagicMock()
        mock_tool_class.return_value = mock_tool

        runner = CliRunner()
        result = runner.invoke(cli, ["test-bucket", "--dry-run"])

        assert result.exit_code == 0
        mock_tool_class.assert_called_once_with(
            dry_run=True, override_key_id=None, override_key=None
        )
        mock_tool.cleanup_unfinished_uploads.assert_called_once_with(
            "test-bucket", interactive=True
        )

    @patch("b2_cleanup.cli.B2CleanupTool")
    def test_cli_with_credentials(self, mock_tool_class):
        """Test CLI with credential overrides."""
        mock_tool = MagicMock()
        mock_tool_class.return_value = mock_tool

        runner = CliRunner()
        result = runner.invoke(
            cli, ["test-bucket", "--key-id", "test-key-id", "--key", "test-key"]
        )

        assert result.exit_code == 0
        mock_tool_class.assert_called_once_with(
            dry_run=False, override_key_id="test-key-id", override_key="test-key"
        )
        mock_tool.cleanup_unfinished_uploads.assert_called_once_with(
            "test-bucket", interactive=True
        )

    @patch("b2_cleanup.cli.B2CleanupTool")
    def test_cli_non_interactive(self, mock_tool_class):
        """Test CLI with non-interactive flag."""
        mock_tool = MagicMock()
        mock_tool_class.return_value = mock_tool

        runner = CliRunner()
        result = runner.invoke(cli, ["test-bucket", "--non-interactive"])

        assert result.exit_code == 0
        mock_tool_class.assert_called_once_with(
            dry_run=False, override_key_id=None, override_key=None
        )
        mock_tool.cleanup_unfinished_uploads.assert_called_once_with(
            "test-bucket", interactive=False
        )

    def test_cli_missing_bucket(self):
        """Test CLI without bucket argument shows interactive selection."""
        runner = CliRunner()
        # Note: We set terminal_width to prevent output truncation in the test result
        result = runner.invoke(cli, [], terminal_width=100)
        
        # Now the command should try to show bucket selection, not error
        assert result.exit_code != 0  # Still non-zero because it gets aborted waiting for input
        assert "Please select a bucket to clean up" in result.output
        assert "Enter the number of the bucket to clean up" in result.output
