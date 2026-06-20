from click.testing import CliRunner

from my_tools.cli import cli


def test_git_help():
    result = CliRunner().invoke(cli, ["git", "--help"])
    assert result.exit_code == 0
    assert "auto" in result.output
    assert "new-branch" in result.output
    assert "delete-branch" in result.output
    assert "open-remote" in result.output
    assert "gitlab-merge-request" in result.output
    assert "copy-change" in result.output
