"""Tests for the CLI interface."""

from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from b2_cleanup.cli import cli


class TestCLI:
    """Test the CLI interface."""

    @patch("b2_cleanup.cli.B2CleanupTool")
    def test_cli_basic(self, mock_tool_class):
        """Test basic CLI functionality."""
        mock_tool = MagicMock()
        mock_tool_class.return_value = mock_tool

        runner = CliRunner()
        result = runner.invoke(cli, ["test-bucket"])

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
        """Test CLI with missing bucket argument."""
        runner = CliRunner()
        result = runner.invoke(cli, [])

        assert result.exit_code != 0
        assert "Missing argument 'BUCKET'" in result.output
