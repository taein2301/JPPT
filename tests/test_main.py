"""Test CLI entry point."""
from jppt.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_version() -> None:
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "jppt" in result.stdout.lower()


def test_cli_help() -> None:
    """Test --help flag."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.stdout
    assert "batch" in result.stdout
