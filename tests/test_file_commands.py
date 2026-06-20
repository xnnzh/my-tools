from pathlib import Path

from click.testing import CliRunner

from my_tools.cli import cli


def test_file_help():
    result = CliRunner().invoke(cli, ["file", "--help"])
    assert result.exit_code == 0
    assert "new-with-template" in result.output
    assert "zip" in result.output


def test_file_new_with_template(tmp_path: Path):
    template = tmp_path / "tpl.txt"
    target = tmp_path / "out.txt"
    template.write_text("time={{NOW_TIME}}", encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["file", "new-with-template", "--template", str(template), "--force", str(target)],
    )

    assert result.exit_code == 0
    assert target.exists()
    assert "time=" in target.read_text(encoding="utf-8")



