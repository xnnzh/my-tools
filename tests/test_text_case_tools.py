from pathlib import Path

import pytest
from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.text.case_tools import (
    convert_case,
    split_words,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)


class TestSplitWords:
    def test_snake(self):
        assert split_words("user_name") == ["user", "name"]

    def test_kebab(self):
        assert split_words("user-name") == ["user", "name"]

    def test_space(self):
        assert split_words("user name") == ["user", "name"]

    def test_camel(self):
        assert split_words("userName") == ["user", "name"]

    def test_pascal(self):
        assert split_words("UserName") == ["user", "name"]

    def test_upper_snake(self):
        assert split_words("USER_NAME") == ["user", "name"]

    def test_dot(self):
        assert split_words("user.name") == ["user", "name"]

    def test_multiple_separators(self):
        assert split_words("user_name-field") == ["user", "name", "field"]

    def test_single_word(self):
        assert split_words("hello") == ["hello"]

    def test_empty(self):
        assert split_words("") == []


class TestToPascalCase:
    def test_snake(self):
        assert to_pascal_case("user_name") == "UserName"

    def test_camel(self):
        assert to_pascal_case("userName") == "UserName"

    def test_single(self):
        assert to_pascal_case("hello") == "Hello"


class TestToCamelCase:
    def test_pascal(self):
        assert to_camel_case("UserName") == "userName"

    def test_snake(self):
        assert to_camel_case("user_name") == "userName"

    def test_single(self):
        assert to_camel_case("Hello") == "hello"


class TestToSnakeCase:
    def test_camel(self):
        assert to_snake_case("userName") == "user_name"

    def test_pascal(self):
        assert to_snake_case("UserName") == "user_name"

    def test_kebab(self):
        assert to_snake_case("user-name") == "user_name"


class TestToKebabCase:
    def test_snake(self):
        assert to_kebab_case("user_name") == "user-name"

    def test_camel(self):
        assert to_kebab_case("userName") == "user-name"

    def test_pascal(self):
        assert to_kebab_case("UserName") == "user-name"


class TestConvertCase:
    def test_pascal(self):
        assert convert_case("user_name", "pascal") == "UserName"

    def test_camel(self):
        assert convert_case("UserName", "camel") == "userName"

    def test_snake(self):
        assert convert_case("userName", "snake") == "user_name"

    def test_kebab(self):
        assert convert_case("user_name", "kebab") == "user-name"

    def test_upper(self):
        assert convert_case("hello", "upper") == "HELLO"

    def test_lower(self):
        assert convert_case("HELLO", "lower") == "hello"

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError, match="不支持"):
            convert_case("hello", "invalid")


class TestCliCase:
    def test_case_help(self):
        result = CliRunner().invoke(cli, ["text", "case", "--help"])
        assert result.exit_code == 0

    def test_upper_help(self):
        result = CliRunner().invoke(cli, ["text", "upper", "--help"])
        assert result.exit_code == 0

    def test_lower_help(self):
        result = CliRunner().invoke(cli, ["text", "lower", "--help"])
        assert result.exit_code == 0

    def test_case_pascal(self):
        result = CliRunner().invoke(
            cli, ["text", "case", "user_name", "--to", "pascal"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "UserName"

    def test_case_camel(self):
        result = CliRunner().invoke(
            cli, ["text", "case", "UserName", "--to", "camel"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "userName"

    def test_case_snake(self):
        result = CliRunner().invoke(
            cli, ["text", "case", "userName", "--to", "snake"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "user_name"

    def test_case_kebab(self):
        result = CliRunner().invoke(
            cli, ["text", "case", "user_name", "--to", "kebab"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "user-name"

    def test_upper(self):
        result = CliRunner().invoke(cli, ["text", "upper", "hello"])
        assert result.exit_code == 0
        assert result.output.strip() == "HELLO"

    def test_lower(self):
        result = CliRunner().invoke(cli, ["text", "lower", "HELLO"])
        assert result.exit_code == 0
        assert result.output.strip() == "hello"

    def test_case_missing_to(self):
        result = CliRunner().invoke(cli, ["text", "case", "hello"])
        assert result.exit_code != 0

    def test_stdin(self):
        result = CliRunner().invoke(cli, ["text", "upper"], input="hello")
        assert result.exit_code == 0
        assert result.output.strip() == "HELLO"

    def test_file_input(self, tmp_path: Path):
        f = tmp_path / "input.txt"
        f.write_text("user_name", encoding="utf-8")
        result = CliRunner().invoke(
            cli, ["text", "case", str(f), "--file", "--to", "pascal"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "UserName"

    def test_output_file(self, tmp_path: Path):
        out = tmp_path / "out.txt"
        result = CliRunner().invoke(
            cli, ["text", "upper", "hello", "-o", str(out)]
        )
        assert result.exit_code == 0
        assert out.read_text(encoding="utf-8") == "HELLO\n"
