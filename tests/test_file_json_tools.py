from pathlib import Path

import pytest
from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.file.json_tools import (
    compact_json,
    escape_json_text,
    pretty_json,
    unescape_json_text,
)


class TestPrettyJson:
    def test_basic(self):
        result = pretty_json('{"b":2,"a":1}')
        assert result == '{\n  "b": 2,\n  "a": 1\n}'

    def test_array(self):
        result = pretty_json('[{"a":1},{"b":2}]')
        assert result == '[\n  {\n    "a": 1\n  },\n  {\n    "b": 2\n  }\n]'

    def test_chinese_default(self):
        result = pretty_json('{"name":"张三"}')
        assert "张三" in result

    def test_ensure_ascii(self):
        result = pretty_json('{"name":"张三"}', ensure_ascii=True)
        assert "张三" not in result
        assert "\\u" in result

    def test_sort_keys(self):
        result = pretty_json('{"b":1,"a":2}', sort_keys=True)
        a_pos = result.index('"a"')
        b_pos = result.index('"b"')
        assert a_pos < b_pos

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="空"):
            pretty_json("")

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="解析失败"):
            pretty_json("not json")

    def test_bom(self):
        result = pretty_json('\ufeff{"a":1}')
        assert result == '{\n  "a": 1\n}'

    def test_indent_negative_raises(self):
        with pytest.raises(ValueError, match="不能小于 0"):
            pretty_json('{"a":1}', indent=-1)

    def test_indent_custom(self):
        result = pretty_json('{"a":1}', indent=4)
        assert result == '{\n    "a": 1\n}'


class TestCompactJson:
    def test_basic(self):
        result = compact_json('{\n  "a": 1,\n  "b": 2\n}')
        assert result == '{"a":1,"b":2}'

    def test_chinese_default(self):
        result = compact_json('{"name":"张三"}')
        assert "张三" in result

    def test_ensure_ascii(self):
        result = compact_json('{"name":"张三"}', ensure_ascii=True)
        assert "\\u" in result

    def test_sort_keys(self):
        result = compact_json('{"b":1,"a":2}', sort_keys=True)
        assert result == '{"a":2,"b":1}'

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="空"):
            compact_json("")

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="解析失败"):
            compact_json("not json")

    def test_nested(self):
        result = compact_json('{"a": {"b": 1}}')
        assert result == '{"a":{"b":1}}'


class TestEscapeJsonText:
    def test_basic(self):
        result = escape_json_text('{"a":1}')
        assert result == '{\\"a\\":1}'

    def test_wrap(self):
        result = escape_json_text('{"a":1}', wrap=True)
        assert result == '"{\\"a\\":1}"'

    def test_newline(self):
        result = escape_json_text("line1\nline2")
        assert "\\n" in result

    def test_chinese_default(self):
        result = escape_json_text("张三")
        assert "张三" in result

    def test_ensure_ascii(self):
        result = escape_json_text("张三", ensure_ascii=True)
        assert "\\u" in result

    def test_empty_string(self):
        result = escape_json_text("")
        assert result == ""

    def test_empty_wrap(self):
        result = escape_json_text("", wrap=True)
        assert result == '""'

    def test_spaces(self):
        result = escape_json_text("  ")
        assert result == "  "

    def test_special_chars(self):
        result = escape_json_text('a"b\\c\td')
        assert result == "a\\\"b\\\\c\\td"


class TestUnescapeJsonText:
    def test_without_wrap(self):
        result = unescape_json_text(r'{\"a\":1}')
        assert result == '{"a":1}'

    def test_with_wrap(self):
        result = unescape_json_text(r'"{\"a\":1}"')
        assert result == '{"a":1}'

    def test_newline(self):
        result = unescape_json_text("line1\\nline2")
        assert result == "line1\nline2"

    def test_chinese(self):
        result = unescape_json_text("张三")
        assert result == "张三"

    def test_empty(self):
        result = unescape_json_text("")
        assert result == ""

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="解析失败"):
            unescape_json_text(r"\invalid")

    def test_number_string(self):
        result = unescape_json_text('"123"')
        assert result == "123"

    def test_unicode_escape(self):
        result = unescape_json_text(r"\u5f20\u4e09")
        assert result == "张三"

    def test_whitespace_padding(self):
        result = unescape_json_text(r'  {\"a\":1}  ')
        assert result == '{"a":1}'


class TestCli:
    def test_group_help_has_json_commands(self):
        result = CliRunner().invoke(cli, ["file", "--help"])
        assert result.exit_code == 0
        assert "json-pretty" in result.output
        assert "json-compact" in result.output
        assert "json-escape" in result.output
        assert "json-unescape" in result.output

    def test_pretty_help(self):
        result = CliRunner().invoke(cli, ["file", "json-pretty", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--encoding" in result.output
        assert "--indent" in result.output
        assert "--sort-keys" in result.output
        assert "--ascii" in result.output

    def test_compact_help(self):
        result = CliRunner().invoke(cli, ["file", "json-compact", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--encoding" in result.output
        assert "--sort-keys" in result.output
        assert "--ascii" in result.output

    def test_escape_help(self):
        result = CliRunner().invoke(cli, ["file", "json-escape", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--encoding" in result.output
        assert "--wrap" in result.output
        assert "--ascii" in result.output

    def test_unescape_help(self):
        result = CliRunner().invoke(cli, ["file", "json-unescape", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--encoding" in result.output

    def test_pretty_stdin(self):
        result = CliRunner().invoke(cli, ["file", "json-pretty"], input='{"a":1}')
        assert result.exit_code == 0
        assert result.output.strip() == '{\n  "a": 1\n}'

    def test_compact_stdin(self):
        result = CliRunner().invoke(
            cli, ["file", "json-compact"], input='{\n  "a": 1\n}'
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"a":1}'

    def test_escape_stdin(self):
        result = CliRunner().invoke(cli, ["file", "json-escape"], input='{"a":1}')
        assert result.exit_code == 0
        assert result.output.strip() == r'{\"a\":1}'

    def test_unescape_stdin(self):
        result = CliRunner().invoke(
            cli, ["file", "json-unescape"], input=r'{\"a\":1}'
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"a":1}'

    def test_pretty_file_input(self, tmp_path: Path):
        data = tmp_path / "data.json"
        data.write_text('{"b":2,"a":1}', encoding="utf-8")
        out = tmp_path / "pretty.json"
        result = CliRunner().invoke(
            cli, ["file", "json-pretty", str(data), "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.read_text(encoding="utf-8") == '{\n  "b": 2,\n  "a": 1\n}\n'

    def test_compact_file_input(self, tmp_path: Path):
        data = tmp_path / "data.json"
        data.write_text('{\n  "a": 1\n}', encoding="utf-8")
        out = tmp_path / "compact.json"
        result = CliRunner().invoke(
            cli, ["file", "json-compact", str(data), "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.read_text(encoding="utf-8") == '{"a":1}\n'

    def test_escape_file_input(self, tmp_path: Path):
        raw = tmp_path / "raw.txt"
        raw.write_text('{"a":1}', encoding="utf-8")
        out = tmp_path / "escaped.txt"
        result = CliRunner().invoke(
            cli, ["file", "json-escape", str(raw), "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.read_text(encoding="utf-8") == r'{\"a\":1}' + "\n"

    def test_unescape_file_input(self, tmp_path: Path):
        escaped = tmp_path / "escaped.txt"
        escaped.write_text(r'{\"a\":1}', encoding="utf-8")
        out = tmp_path / "raw.txt"
        result = CliRunner().invoke(
            cli, ["file", "json-unescape", str(escaped), "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.read_text(encoding="utf-8") == '{"a":1}\n'

    def test_pretty_invalid_json_fails(self):
        result = CliRunner().invoke(
            cli, ["file", "json-pretty"], input="not json"
        )
        assert result.exit_code != 0

    def test_compact_invalid_json_fails(self):
        result = CliRunner().invoke(
            cli, ["file", "json-compact"], input="not json"
        )
        assert result.exit_code != 0

    def test_unescape_invalid_fails(self):
        result = CliRunner().invoke(
            cli, ["file", "json-unescape"], input=r"\invalid"
        )
        assert result.exit_code != 0

    def test_escape_any_text_ok(self):
        result = CliRunner().invoke(cli, ["file", "json-escape"], input="any text")
        assert result.exit_code == 0
        assert result.output.strip() == "any text"

    def test_pretty_sort_keys(self):
        result = CliRunner().invoke(
            cli, ["file", "json-pretty", "--sort-keys"], input='{"b":1,"a":2}'
        )
        assert result.exit_code == 0
        a_pos = result.output.index('"a"')
        b_pos = result.output.index('"b"')
        assert a_pos < b_pos

    def test_pretty_indent_custom(self):
        result = CliRunner().invoke(
            cli, ["file", "json-pretty", "--indent", "4"], input='{"a":1}'
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{\n    "a": 1\n}'

    def test_escape_wrap(self):
        result = CliRunner().invoke(
            cli, ["file", "json-escape", "--wrap"], input='{"a":1}'
        )
        assert result.exit_code == 0
        assert result.output.strip() == r'"{\"a\":1}"'

    def test_compact_sort_keys(self):
        result = CliRunner().invoke(
            cli, ["file", "json-compact", "--sort-keys"], input='{"b":1,"a":2}'
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"a":2,"b":1}'

    def test_ascii_flag(self):
        result = CliRunner().invoke(
            cli, ["file", "json-pretty", "--ascii"], input='{"name":"张三"}'
        )
        assert result.exit_code == 0
        assert "\\u5f20\\u4e09" in result.output
