from pathlib import Path

from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.file.reverse import reverse_lines


def test_reverse_lines_basic():
    assert reverse_lines("a\nb\nc") == "c\nb\na"


def test_reverse_lines_single_line():
    assert reverse_lines("hello") == "hello"


def test_reverse_lines_empty():
    assert reverse_lines("") == ""


def test_reverse_lines_keep_empty():
    assert reverse_lines("a\n\nb\n\nc\n") == "c\n\nb\n\na"


def test_reverse_lines_discard_empty():
    result = reverse_lines("a\n\nb\n   \nc", keep_empty=False)
    assert result == "c\nb\na"


def test_reverse_lines_all_empty_discard():
    assert reverse_lines("\n\n  \n", keep_empty=False) == ""


def test_reverse_lines_trailing_newline():
    assert reverse_lines("a\nb\nc\n") == "c\nb\na"


def test_cli_help():
    result = CliRunner().invoke(cli, ["file", "reverse", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--encoding" in result.output
    assert "--keep-empty" in result.output
    assert "--strip-trailing-newline" in result.output


def test_cli_file_command_listed():
    result = CliRunner().invoke(cli, ["file", "--help"])
    assert result.exit_code == 0
    assert "reverse" in result.output


def test_cli_stdin():
    result = CliRunner().invoke(
        cli, ["file", "reverse"], input="a\nb\nc\n"
    )
    assert result.exit_code == 0
    assert result.output == "c\nb\na\n"


def test_cli_basic_file(tmp_path: Path):
    f = tmp_path / "input.txt"
    f.write_text("a\nb\nc\n")
    result = CliRunner().invoke(cli, ["file", "reverse", str(f)])
    assert result.exit_code == 0
    assert result.output == "c\nb\na\n"


def test_cli_output_file(tmp_path: Path):
    f = tmp_path / "input.txt"
    out = tmp_path / "out.txt"
    f.write_text("a\nb\nc\n")
    result = CliRunner().invoke(
        cli, ["file", "reverse", str(f), "-o", str(out)]
    )
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8") == "c\nb\na\n"


def test_cli_no_keep_empty(tmp_path: Path):
    f = tmp_path / "input.txt"
    f.write_text("a\n\nb\n   \nc\n")
    result = CliRunner().invoke(
        cli, ["file", "reverse", str(f), "--no-keep-empty"]
    )
    assert result.exit_code == 0
    assert result.output == "c\nb\na\n"


def test_cli_strip_trailing_newline(tmp_path: Path):
    f = tmp_path / "input.txt"
    f.write_text("a\nb\nc\n")
    result = CliRunner().invoke(
        cli, ["file", "reverse", str(f), "--strip-trailing-newline"]
    )
    assert result.exit_code == 0
    assert result.output == "c\nb\na"


def test_cli_custom_encoding(tmp_path: Path):
    f = tmp_path / "input.txt"
    f.write_bytes("a\nb\nc\n".encode("gbk"))
    result = CliRunner().invoke(
        cli, ["file", "reverse", str(f), "--encoding", "gbk"]
    )
    assert result.exit_code == 0
    assert result.output == "c\nb\na\n"
