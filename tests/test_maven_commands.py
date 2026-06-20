from click.testing import CliRunner

from my_tools.cli import cli


def test_maven_help():
    result = CliRunner().invoke(cli, ["maven", "--help"])
    assert result.exit_code == 0
    assert "simple" in result.output
