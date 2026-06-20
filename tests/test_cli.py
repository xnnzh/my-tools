from click.testing import CliRunner

from my_tools.cli import cli


def test_cli_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "git" in result.output
    assert "file" in result.output
    assert "maven" in result.output
    assert "db" in result.output


def test_list():
    result = CliRunner().invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "my-tools git auto" in result.output
    assert "my-tools db batch-delete" in result.output
