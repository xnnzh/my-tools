from click.testing import CliRunner

from my_tools.cli import cli


def test_completion_help():
    result = CliRunner().invoke(cli, ["completion", "--help"])
    assert result.exit_code == 0
    assert "show" in result.output
    assert "install" in result.output


def test_completion_show_zsh():
    result = CliRunner().invoke(cli, ["completion", "show", "--shell", "zsh"])
    assert result.exit_code == 0
    assert "#compdef my-tools" in result.output


def test_completion_show_bash():
    result = CliRunner().invoke(cli, ["completion", "show", "--shell", "bash"])
    assert result.exit_code == 0
    assert "_my-tools_completion" in result.output or "complete" in result.output


def test_completion_show_fish():
    result = CliRunner().invoke(cli, ["completion", "show", "--shell", "fish"])
    assert result.exit_code == 0
    assert "--command my-tools" in result.output


def test_completion_show_invalid_shell():
    result = CliRunner().invoke(cli, ["completion", "show", "--shell", "csh"])
    assert result.exit_code != 0
    assert "csh" in result.output


def test_completion_show_missing_shell():
    result = CliRunner().invoke(cli, ["completion", "show"])
    assert result.exit_code != 0


def test_completion_install_zsh(tmp_path, monkeypatch):
    monkeypatch.setattr("my_tools.completion.commands.Path.home", lambda: tmp_path)
    result = CliRunner().invoke(cli, ["completion", "install", "--shell", "zsh"])
    assert result.exit_code == 0
    target = tmp_path / ".config" / "my-tools" / "completions" / "my-tools.zsh"
    assert target.exists()
    assert "#compdef my-tools" in target.read_text()


def test_completion_install_bash(tmp_path, monkeypatch):
    monkeypatch.setattr("my_tools.completion.commands.Path.home", lambda: tmp_path)
    result = CliRunner().invoke(cli, ["completion", "install", "--shell", "bash"])
    assert result.exit_code == 0
    target = tmp_path / ".config" / "my-tools" / "completions" / "my-tools.bash"
    assert target.exists()


def test_completion_install_fish(tmp_path, monkeypatch):
    monkeypatch.setattr("my_tools.completion.commands.Path.home", lambda: tmp_path)
    result = CliRunner().invoke(cli, ["completion", "install", "--shell", "fish"])
    assert result.exit_code == 0
    target = tmp_path / ".config" / "fish" / "completions" / "my-tools.fish"
    assert target.exists()
