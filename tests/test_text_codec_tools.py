from pathlib import Path

import pytest
from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.text.codec_tools import (
    _check_invalid_percent,
    decode_base_text,
    decode_unicode_text,
    decode_url_text,
    decode_utf8_text,
    encode_base_text,
    encode_unicode_text,
    encode_url_text,
    encode_utf8_text,
)


class TestEncodeUnicode:
    def test_chinese(self):
        assert encode_unicode_text("你好") == r"\u4f60\u597d"

    def test_mixed(self):
        assert encode_unicode_text("hello你好") == r"hello\u4f60\u597d"

    def test_emoji(self):
        result = encode_unicode_text("😀")
        assert result == r"\ud83d\ude00"

    def test_ascii_only(self):
        assert encode_unicode_text("hello") == "hello"


class TestDecodeUnicode:
    def test_chinese(self):
        assert decode_unicode_text(r"\u4f60\u597d") == "你好"

    def test_emoji_surrogate(self):
        assert decode_unicode_text(r"\ud83d\ude00") == "😀"

    def test_capital_u_8_digits(self):
        assert decode_unicode_text(r"\U00004f60") == "你"

    def test_plain_text_unchanged(self):
        assert decode_unicode_text(r"line1\n你") == r"line1\n你"

    def test_invalid_escape_raises(self):
        with pytest.raises(ValueError, match="孤立代理项"):
            decode_unicode_text(r"\ud800")

    def test_invalid_hex_raises(self):
        with pytest.raises(ValueError, match="不是合法十六进制"):
            decode_unicode_text(r"\uZZZZ")

    def test_incomplete_escape_raises(self):
        with pytest.raises(ValueError, match="不足"):
            decode_unicode_text(r"\u123")

    def test_capital_u_requires_8_digits(self):
        with pytest.raises(ValueError, match="不足"):
            decode_unicode_text(r"\U4f60")


class TestEncodeUtf8:
    def test_chinese(self):
        assert encode_utf8_text("你好") == "e4 bd a0 e5 a5 bd"

    def test_ascii(self):
        assert encode_utf8_text("hello") == "68 65 6c 6c 6f"

    def test_empty(self):
        assert encode_utf8_text("") == ""


class TestDecodeUtf8:
    def test_spaced_hex(self):
        assert decode_utf8_text("e4 bd a0 e5 a5 bd") == "你好"

    def test_continuous_hex(self):
        assert decode_utf8_text("e4bda0e5a5bd") == "你好"

    def test_backslash_x(self):
        assert decode_utf8_text(r"\xe4\xbd\xa0\xe5\xa5\xbd") == "你好"

    def test_0x_prefix(self):
        assert decode_utf8_text("0xe4 0xbd 0xa0") == "你"

    def test_mixed(self):
        assert decode_utf8_text("e4 bd a0") == "你"

    def test_odd_length_raises(self):
        with pytest.raises(ValueError, match="奇数"):
            decode_utf8_text("e4 b")

    def test_non_hex_raises(self):
        with pytest.raises(ValueError, match="非 hex"):
            decode_utf8_text("zz")

    def test_invalid_utf8_raises(self):
        with pytest.raises(ValueError):
            decode_utf8_text("ff")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="为空"):
            decode_utf8_text("")


class TestEncodeUrl:
    def test_chinese_and_special(self):
        result = encode_url_text("你好 world?a=1&b=2")
        assert result == "%E4%BD%A0%E5%A5%BD%20world%3Fa%3D1%26b%3D2"

    def test_safe_slash(self):
        result = encode_url_text("/a b", safe="/")
        assert result == "/a%20b"

    def test_plus(self):
        result = encode_url_text("a b", plus=True)
        assert result == "a+b"

    def test_ascii(self):
        assert encode_url_text("hello") == "hello"


class TestDecodeUrl:
    def test_chinese(self):
        result = decode_url_text("%E4%BD%A0%E5%A5%BD%20world")
        assert result == "你好 world"

    def test_plus(self):
        result = decode_url_text("a+b", plus=True)
        assert result == "a b"

    def test_plus_default(self):
        result = decode_url_text("a+b")
        assert result == "a+b"

    def test_ascii(self):
        assert decode_url_text("hello") == "hello"


class TestCheckInvalidPercent:
    def test_valid(self):
        _check_invalid_percent("%E4%BD%20")
        assert True

    def test_no_percent(self):
        _check_invalid_percent("hello")
        assert True

    def test_incomplete_raises(self):
        with pytest.raises(ValueError, match="不完整"):
            _check_invalid_percent("abc%")

    def test_invalid_hex_raises(self):
        with pytest.raises(ValueError, match="不是合法十六进制"):
            _check_invalid_percent("abc%zz")


class TestEncodeBase:
    def test_base64(self):
        assert encode_base_text("hello") == "aGVsbG8="

    def test_base64_chinese(self):
        assert encode_base_text("你好") == "5L2g5aW9"

    def test_base16(self):
        result = encode_base_text("hello", base="16")
        assert result == "68656C6C6F"

    def test_base32(self):
        result = encode_base_text("hello", base="32")
        assert result == "NBSWY3DP"

    def test_base85(self):
        result = encode_base_text("hello", base="85")
        assert result == "Xk~0{Zv"

    def test_invalid_base(self):
        with pytest.raises(ValueError, match="不支持"):
            encode_base_text("hello", base="99")


class TestDecodeBase:
    def test_base64(self):
        assert decode_base_text("aGVsbG8=") == "hello"

    def test_base64_chinese(self):
        assert decode_base_text("5L2g5aW9") == "你好"

    def test_base64_with_newlines(self):
        assert decode_base_text("aGVs\nbG8=") == "hello"

    def test_base16(self):
        assert decode_base_text("68656C6C6F", base="16") == "hello"

    def test_base32(self):
        assert decode_base_text("NBSWY3DP", base="32") == "hello"

    def test_base85(self):
        assert decode_base_text("Xk~0{Zv", base="85") == "hello"

    def test_invalid_base64_raises(self):
        with pytest.raises(ValueError):
            decode_base_text("!!!bad!!!")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="为空"):
            decode_base_text("")


class TestCliCodec:
    def test_group_help_has_commands(self):
        result = CliRunner().invoke(cli, ["text", "--help"])
        assert result.exit_code == 0
        assert "unicode-encode" in result.output
        assert "unicode-decode" in result.output
        assert "utf8-encode" in result.output
        assert "utf8-decode" in result.output
        assert "url-encode" in result.output
        assert "url-decode" in result.output
        assert "base-encode" in result.output
        assert "base-decode" in result.output
        assert "case" in result.output
        assert "upper" in result.output
        assert "lower" in result.output

    def test_unicode_encode_help(self):
        result = CliRunner().invoke(cli, ["text", "unicode-encode", "--help"])
        assert result.exit_code == 0

    def test_unicode_decode_help(self):
        result = CliRunner().invoke(cli, ["text", "unicode-decode", "--help"])
        assert result.exit_code == 0

    def test_utf8_encode_help(self):
        result = CliRunner().invoke(cli, ["text", "utf8-encode", "--help"])
        assert result.exit_code == 0

    def test_utf8_decode_help(self):
        result = CliRunner().invoke(cli, ["text", "utf8-decode", "--help"])
        assert result.exit_code == 0

    def test_url_encode_help(self):
        result = CliRunner().invoke(cli, ["text", "url-encode", "--help"])
        assert result.exit_code == 0

    def test_url_decode_help(self):
        result = CliRunner().invoke(cli, ["text", "url-decode", "--help"])
        assert result.exit_code == 0

    def test_base_encode_help(self):
        result = CliRunner().invoke(cli, ["text", "base-encode", "--help"])
        assert result.exit_code == 0

    def test_base_decode_help(self):
        result = CliRunner().invoke(cli, ["text", "base-decode", "--help"])
        assert result.exit_code == 0

    def test_unicode_encode_arg(self):
        result = CliRunner().invoke(cli, ["text", "unicode-encode", "你好"])
        assert result.exit_code == 0
        assert result.output.strip() == r"\u4f60\u597d"

    def test_unicode_decode_arg(self):
        result = CliRunner().invoke(
            cli, ["text", "unicode-decode", r"\u4f60\u597d"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "你好"

    def test_unicode_decode_invalid_fails(self):
        result = CliRunner().invoke(cli, ["text", "unicode-decode", r"\uZZZZ"])
        assert result.exit_code != 0

    def test_unicode_decode_incomplete_fails(self):
        result = CliRunner().invoke(cli, ["text", "unicode-decode", r"\u123"])
        assert result.exit_code != 0

    def test_unicode_decode_capital_u_requires_8(self):
        result = CliRunner().invoke(cli, ["text", "unicode-decode", r"\U4f60"])
        assert result.exit_code != 0

    def test_utf8_encode_arg(self):
        result = CliRunner().invoke(cli, ["text", "utf8-encode", "你好"])
        assert result.exit_code == 0
        assert result.output.strip() == "e4 bd a0 e5 a5 bd"

    def test_utf8_decode_arg(self):
        result = CliRunner().invoke(
            cli, ["text", "utf8-decode", "e4 bd a0 e5 a5 bd"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "你好"

    def test_utf8_decode_invalid_fails(self):
        result = CliRunner().invoke(cli, ["text", "utf8-decode", "ff"])
        assert result.exit_code != 0

    def test_url_encode_arg(self):
        result = CliRunner().invoke(cli, ["text", "url-encode", "你好 world?a=1&b=2"])
        assert result.exit_code == 0
        assert result.output.strip() == "%E4%BD%A0%E5%A5%BD%20world%3Fa%3D1%26b%3D2"

    def test_url_decode_arg(self):
        result = CliRunner().invoke(
            cli,
            ["text", "url-decode", "%E4%BD%A0%E5%A5%BD%20world%3Fa%3D1%26b%3D2"],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '你好 world?a=1&b=2'

    def test_url_decode_invalid_fails(self):
        result = CliRunner().invoke(cli, ["text", "url-decode", "abc%zz"])
        assert result.exit_code != 0

    def test_base_encode_arg(self):
        result = CliRunner().invoke(cli, ["text", "base-encode", "你好"])
        assert result.exit_code == 0
        assert result.output.strip() == "5L2g5aW9"

    def test_base_decode_arg(self):
        result = CliRunner().invoke(cli, ["text", "base-decode", "5L2g5aW9"])
        assert result.exit_code == 0
        assert result.output.strip() == "你好"

    def test_base_decode_invalid_fails(self):
        result = CliRunner().invoke(cli, ["text", "base-decode", "bad"])
        assert result.exit_code != 0

    def test_base_decode_invalid_chars_fails(self):
        result = CliRunner().invoke(cli, ["text", "base-decode", "aGVsbG8=!!!!"])
        assert result.exit_code != 0

    def test_stdin_input(self):
        result = CliRunner().invoke(cli, ["text", "url-encode"], input="你好 world")
        assert result.exit_code == 0
        assert result.output.strip() == "%E4%BD%A0%E5%A5%BD%20world"

    def test_file_input(self, tmp_path: Path):
        f = tmp_path / "input.txt"
        f.write_text("你好 world", encoding="utf-8")
        result = CliRunner().invoke(
            cli, ["text", "url-encode", str(f), "--file"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "%E4%BD%A0%E5%A5%BD%20world"

    def test_output_file(self, tmp_path: Path):
        out = tmp_path / "out.txt"
        result = CliRunner().invoke(
            cli, ["text", "url-encode", "你好", "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.read_text(encoding="utf-8") == "%E4%BD%A0%E5%A5%BD\n"

    def test_missing_file_flag_raises(self):
        result = CliRunner().invoke(
            cli, ["text", "url-encode", "--file"]
        )
        assert result.exit_code != 0
