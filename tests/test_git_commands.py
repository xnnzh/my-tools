from unittest.mock import patch

from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.core.completion import complete_git_branches


def test_complete_git_branches_filters_by_prefix():
    with patch(
        "my_tools.core.completion.capture",
        return_value="main\nfeature/a\nfeature/b\nbugfix/c\n",
    ):
        items = complete_git_branches(None, None, "feature/")

    assert [item.value for item in items] == ["feature/a", "feature/b"]


def test_complete_git_branches_returns_empty_on_error():
    with patch("my_tools.core.completion.capture", side_effect=RuntimeError("not git")):
        assert complete_git_branches(None, None, "") == []


def test_git_help():
    result = CliRunner().invoke(cli, ["git", "--help"])
    assert result.exit_code == 0
    assert "auto" in result.output
    assert "new-branch" in result.output
    assert "delete-branch" in result.output
    assert "open-remote" in result.output
    assert "gitlab-merge-request" in result.output
    assert "copy-change" in result.output
