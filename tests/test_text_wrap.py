from pathlib import Path

from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.text.wrap import wrap_lines


class TestWrapLines:
    def test_basic_prefix_suffix(self):
        result = wrap_lines("a\nb\nc", "'", suffix="',")
        assert result == "'a',\n'b',\n'c',"

    def test_last_suffix(self):
        result = wrap_lines("1\n2\n3", "'", suffix="',", last_suffix="'")
        assert result == "'1',\n'2',\n'3'"

    def test_single_line_with_last_suffix(self):
        result = wrap_lines("hello", "(", suffix=")", last_suffix="!")
        assert result == "(hello!"

    def test_single_line_without_last_suffix(self):
        result = wrap_lines("hello", "(", suffix=")")
        assert result == "(hello)"

    def test_empty_input(self):
        result = wrap_lines("", "--")
        assert result == ""

    def test_skip_empty_lines_by_default(self):
        text = "a\n\n\nb\nc"
        result = wrap_lines(text, ">", suffix="<")
        assert result == ">a<\n>b<\n>c<"

    def test_keep_empty_lines(self):
        text = "a\n\nb"
        result = wrap_lines(text, ">", suffix="<", keep_empty=True)
        assert result == ">a<\n><\n>b<"

    def test_only_empty_lines_skipped(self):
        result = wrap_lines("\n\n\n", "x")
        assert result == ""

    def test_only_empty_lines_kept(self):
        result = wrap_lines("\n\n", "x", keep_empty=True)
        assert result == "x\nx"

    def test_empty_prefix(self):
        result = wrap_lines("a\nb", "", suffix=",")
        assert result == "a,\nb,"

    def test_default_suffix_and_last_suffix(self):
        result = wrap_lines("a\nb\nc", ">>")
        assert result == ">>a\n>>b\n>>c"

    def test_last_suffix_same_as_suffix(self):
        result = wrap_lines("a\nb\nc", ">", suffix="<", last_suffix="<")
        assert result == ">a<\n>b<\n>c<"

    def test_blank_lines_with_whitespace_only(self):
        text = "a\n  \n\t\nb"
        result = wrap_lines(text, "'", suffix="',")
        assert result == "'a',\n'b',"


class TestCliWrap:
    def test_wrap_help(self):
        result = CliRunner().invoke(cli, ["text", "wrap", "--help"])
        assert result.exit_code == 0

    def test_basic_stdin(self):
        result = CliRunner().invoke(
            cli, ["text", "wrap", "--prefix", "'", "--suffix", "',", "--last-suffix", "'"],
            input="1\n2\n3",
        )
        assert result.exit_code == 0
        assert result.output.strip() == "'1',\n'2',\n'3'"

    def test_basic_file(self, tmp_path: Path):
        f = tmp_path / "input.txt"
        f.write_text("1\n2\n3", encoding="utf-8")
        result = CliRunner().invoke(
            cli, ["text", "wrap", str(f), "--prefix", "'", "--suffix", "',", "--last-suffix", "'"],
        )
        assert result.exit_code == 0
        assert result.output.strip() == "'1',\n'2',\n'3'"

    def test_keep_empty(self):
        result = CliRunner().invoke(
            cli, ["text", "wrap", "--prefix", ">", "--keep-empty"],
            input="a\n\nb",
        )
        assert result.exit_code == 0
        assert result.output.strip() == ">a\n>\n>b"

    def test_skip_empty_default(self):
        result = CliRunner().invoke(
            cli, ["text", "wrap", "--prefix", ">"],
            input="a\n\n\nb",
        )
        assert result.exit_code == 0
        assert result.output.strip() == ">a\n>b"

    def test_output_file(self, tmp_path: Path):
        out = tmp_path / "out.txt"
        result = CliRunner().invoke(
            cli, ["text", "wrap", "--prefix", ">", "-o", str(out)],
            input="a\nb",
        )
        assert result.exit_code == 0
        assert out.read_text(encoding="utf-8") == ">a\n>b\n"

    def test_missing_prefix_fails(self):
        result = CliRunner().invoke(cli, ["text", "wrap"], input="a")
        assert result.exit_code != 0

    def test_only_prefix(self):
        result = CliRunner().invoke(
            cli, ["text", "wrap", "--prefix", ">"],
            input="a\nb\nc",
        )
        assert result.exit_code == 0
        assert result.output.strip() == ">a\n>b\n>c"
