from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.db.mybatis_sql import (
    SqlValue,
    format_mybatis_log,
    inline_parameters,
    parse_parameter_list,
    to_sql_literal,
)


def test_to_sql_literal_null():
    assert to_sql_literal(SqlValue(raw=None)) == "NULL"


def test_to_sql_literal_null_with_type():
    assert to_sql_literal(SqlValue(raw=None, type_name="String")) == "NULL"


def test_to_sql_literal_numeric():
    assert to_sql_literal(SqlValue(raw="123", type_name="Integer")) == "123"
    assert to_sql_literal(SqlValue(raw="456", type_name="Long")) == "456"
    assert to_sql_literal(SqlValue(raw="78.9", type_name="BigDecimal")) == "78.9"


def test_to_sql_literal_boolean():
    assert to_sql_literal(SqlValue(raw="true", type_name="Boolean")) == "TRUE"
    assert to_sql_literal(SqlValue(raw="false", type_name="Boolean")) == "FALSE"


def test_to_sql_literal_string():
    assert to_sql_literal(SqlValue(raw="Bob", type_name="String")) == "'Bob'"


def test_to_sql_literal_string_escape():
    assert to_sql_literal(SqlValue(raw="O'Brien", type_name="String")) == "'O''Brien'"


def test_to_sql_literal_date():
    assert to_sql_literal(SqlValue(raw="2024-01-01", type_name="Date")) == "'2024-01-01'"


def test_to_sql_literal_timestamp():
    actual = to_sql_literal(
        SqlValue(raw="2024-01-01 12:30:00", type_name="Timestamp")
    )
    assert actual == "'2024-01-01 12:30:00'"


def test_to_sql_literal_unknown_type():
    assert to_sql_literal(SqlValue(raw="foo", type_name="CustomType")) == "'foo'"


def test_to_sql_literal_no_type():
    assert to_sql_literal(SqlValue(raw="foo")) == "'foo'"


def test_parse_parameter_list_basic():
    params = parse_parameter_list("1(Long), Bob(String)")
    assert params == [
        SqlValue(raw="1", type_name="Long"),
        SqlValue(raw="Bob", type_name="String"),
    ]


def test_parse_parameter_list_null():
    params = parse_parameter_list("null, 1(Long)")
    assert params == [
        SqlValue(raw=None),
        SqlValue(raw="1", type_name="Long"),
    ]


def test_parse_parameter_list_null_with_type():
    params = parse_parameter_list("null(String), 1(Long)")
    assert params == [
        SqlValue(raw=None, type_name="String"),
        SqlValue(raw="1", type_name="Long"),
    ]


def test_parse_parameter_list_date():
    params = parse_parameter_list("2024-01-01(Date), true(Boolean)")
    assert params == [
        SqlValue(raw="2024-01-01", type_name="Date"),
        SqlValue(raw="true", type_name="Boolean"),
    ]


def test_parse_parameter_list_comma_in_string():
    params = parse_parameter_list("Alice,Bob(String), 1(Long)")
    assert params == [
        SqlValue(raw="Alice,Bob", type_name="String"),
        SqlValue(raw="1", type_name="Long"),
    ]


def test_parse_parameter_list_single():
    params = parse_parameter_list("42(Integer)")
    assert params == [SqlValue(raw="42", type_name="Integer")]


def test_inline_parameters_basic():
    params = [SqlValue(raw="1", type_name="Long"), SqlValue(raw="Bob", type_name="String")]
    result, warns = inline_parameters(
        "select * from user where id = ? and name = ?", params
    )
    assert result == "select * from user where id = 1 and name = 'Bob'"
    assert warns == []


def test_inline_parameters_semicolon_added():
    text = "==>  Preparing: select * from user where id = ? and name = ?\n==> Parameters: 1(Long), Bob(String)"
    result, warns = format_mybatis_log(text)
    assert result == "select * from user where id = 1 and name = 'Bob';\n"
    assert warns == []


def test_inline_parameters_already_has_semicolon():
    text = "==>  Preparing: select * from user where id = ?;\n==> Parameters: 1(Long)"
    result, warns = format_mybatis_log(text)
    assert result == "select * from user where id = 1;\n"
    assert warns == []


def test_inline_parameters_null():
    params = [SqlValue(raw=None)]
    result, warns = inline_parameters("select * from user where id = ?", params)
    assert result == "select * from user where id = NULL"
    assert warns == []


def test_inline_parameters_boolean():
    params = [SqlValue(raw="true", type_name="Boolean")]
    result, warns = inline_parameters("select * from user where active = ?", params)
    assert result == "select * from user where active = TRUE"
    assert warns == []


def test_inline_parameters_string_escape():
    params = [SqlValue(raw="O'Brien", type_name="String")]
    result, warns = inline_parameters(
        "select * from user where name = ?", params
    )
    assert result == "select * from user where name = 'O''Brien'"
    assert warns == []


def test_inline_parameters_date():
    params = [SqlValue(raw="2024-01-01", type_name="Date")]
    result, warns = inline_parameters(
        "select * from user where birthday = ?", params
    )
    assert result == "select * from user where birthday = '2024-01-01'"
    assert warns == []


def test_inline_parameters_timestamp():
    params = [SqlValue(raw="2024-01-01 12:30:00", type_name="Timestamp")]
    result, warns = inline_parameters(
        "select * from payment where create_time = ?", params
    )
    assert result == "select * from payment where create_time = '2024-01-01 12:30:00'"
    assert warns == []


def test_inline_parameters_comma_in_value():
    params = [SqlValue(raw="Alice,Bob", type_name="String")]
    result, warns = inline_parameters(
        "select * from user where name = ?", params
    )
    assert result == "select * from user where name = 'Alice,Bob'"
    assert warns == []


def test_inline_parameters_question_mark_in_string_literal():
    params = [SqlValue(raw="1", type_name="Long")]
    result, warns = inline_parameters(
        "select '?' as q, `a?b` from user -- ?\nwhere id = ?", params
    )
    assert result == "select '?' as q, `a?b` from user -- ?\nwhere id = 1"
    assert warns == []


def test_inline_parameters_mismatch_too_few_params_non_strict():
    params = [SqlValue(raw="1", type_name="Long")]
    result, warns = inline_parameters(
        "select * from user where id = ? and name = ?", params
    )
    assert "?" in result
    assert warns != []


def test_inline_parameters_mismatch_too_few_params_strict():
    params = [SqlValue(raw="1", type_name="Long")]
    result, warns = inline_parameters(
        "select * from user where id = ? and name = ?",
        params,
        strict=True,
    )
    assert result == ""
    assert warns != []


def test_format_simple_replace():
    log = (
        "2026-06-21 INFO start clean task\n"
        "==>  Preparing: select * from user where id = ? and name = ?\n"
        "==> Parameters: 1(Long), Bob(String)\n"
        "2026-06-21 INFO finish clean task\n"
    )
    result, warns = format_mybatis_log(log)
    assert "2026-06-21 INFO start clean task" in result
    assert "2026-06-21 INFO finish clean task" in result
    assert "select * from user where id = 1 and name = 'Bob';" in result
    assert "Preparing:" not in result
    assert "Parameters:" not in result
    assert warns == []


def test_format_append():
    log = (
        "2026-06-21 INFO start clean task\n"
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "2026-06-21 INFO finish clean task\n"
    )
    result, warns = format_mybatis_log(log, mode="append")
    assert "2026-06-21 INFO start clean task" in result
    assert "==>  Preparing:" in result
    assert "==> Parameters:" in result
    assert "-- Formatted SQL:" in result
    assert "select * from user where id = 1;" in result
    assert warns == []


def test_format_sql_only():
    log = (
        "2026-06-21 INFO\n"
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "garbage\n"
    )
    result, warns = format_mybatis_log(log, mode="sql-only")
    assert result == "select * from user where id = 1;"
    assert "2026-06-21 INFO" not in result
    assert warns == []


def test_format_sql_only_multi():
    log = (
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "---\n"
        "==>  Preparing: select * from order where id = ?\n"
        "==> Parameters: 2(Long)\n"
    )
    result, warns = format_mybatis_log(log, mode="sql-only", blank_line=True)
    assert "select * from user where id = 1;" in result
    assert "select * from order where id = 2;" in result
    assert "\n\n" in result
    assert warns == []


def test_format_sql_only_no_blank_line():
    log = (
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "==>  Preparing: select * from order where id = ?\n"
        "==> Parameters: 2(Long)\n"
    )
    result, warns = format_mybatis_log(log, mode="sql-only", blank_line=False)
    lines = result.splitlines()
    assert len(lines) == 2
    assert warns == []


def test_format_sql_no_params():
    log = "==>  Preparing: select * from user where id = 1\n"
    result, warns = format_mybatis_log(log, mode="replace")
    assert "select * from user where id = 1;" in result
    assert warns == []


def test_format_sql_no_params_with_placeholder():
    log = "==>  Preparing: select * from user where id = ?\n"
    result, warns = format_mybatis_log(log, strict=False)
    assert "?" in result
    assert warns != []


def test_format_sql_no_params_with_placeholder_strict():
    log = "==>  Preparing: select * from user where id = ?\n"
    result, warns = format_mybatis_log(log, strict=True)
    assert result == ""
    assert warns != []


def test_format_reuses_no_semicolon():
    log = "==>  Preparing: select * from user where id = ?\n==> Parameters: 1(Long)\n"
    result, warns = format_mybatis_log(log, semicolon=False)
    assert result == "select * from user where id = 1\n"
    assert warns == []


def test_format_handles_missing_linebreaks():
    log = "==>  Preparing: select * from user where id = ?\n==> Parameters: 1(Long)\n"
    result, warns = format_mybatis_log(log)
    assert "select * from user where id = 1;" in result
    assert warns == []


def test_format_non_mybatis_lines_preserved_in_replace():
    log = (
        "2026-06-21 DEBUG starting\n"
        "==>  Preparing: select 1\n"
        "==> Parameters: 1(Long)\n"
        "2026-06-21 DEBUG done\n"
    )
    result, warns = format_mybatis_log(log)
    lines = result.splitlines()
    assert lines[0] == "2026-06-21 DEBUG starting"
    assert lines[1] == "select 1;"
    assert lines[2] == "2026-06-21 DEBUG done"
    assert not result.startswith("==>")


def test_format_multiple_sql_blocks():
    log = (
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "==>  Preparing: select * from order where id = ?\n"
        "==> Parameters: 2(Long)\n"
    )
    result, warns = format_mybatis_log(log)
    assert "select * from user where id = 1;" in result
    assert "select * from order where id = 2;" in result
    assert warns == []


def test_format_mixed_line_prefixes():
    log = (
        "2026-06-21 DEBUG ==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
    )
    result, warns = format_mybatis_log(log)
    assert "select * from user where id = 1;" in result
    assert warns == []


def test_cli_mybatis_sql_help():
    result = CliRunner().invoke(cli, ["db", "mybatis-sql", "--help"])
    assert result.exit_code == 0
    assert "--mode" in result.output
    assert "--strict" in result.output
    assert "--semicolon" in result.output
    assert "--blank-line" in result.output


def test_cli_mybatis_sql_stdin():
    log = (
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
    )
    result = CliRunner().invoke(cli, ["db", "mybatis-sql"], input=log)
    assert result.exit_code == 0
    assert "select * from user where id = 1;" in result.output


def test_cli_mybatis_sql_stdin_append():
    log = (
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
    )
    result = CliRunner().invoke(cli, ["db", "mybatis-sql", "--mode", "append"], input=log)
    assert result.exit_code == 0
    assert "Preparing:" in result.output
    assert "Parameters:" in result.output
    assert "-- Formatted SQL:" in result.output
    assert "select * from user where id = 1;" in result.output


def test_cli_mybatis_sql_stdin_sql_only():
    log = (
        "garbage\n"
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "more garbage\n"
    )
    result = CliRunner().invoke(cli, ["db", "mybatis-sql", "--mode", "sql-only"], input=log)
    assert result.exit_code == 0
    assert "select * from user where id = 1;" in result.output
    assert "garbage" not in result.output


def test_cli_mybatis_sql_file_input(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
    )
    result = CliRunner().invoke(cli, ["db", "mybatis-sql", str(log_file)])
    assert result.exit_code == 0
    assert "select * from user where id = 1;" in result.output


def test_cli_mybatis_sql_strict_fails():
    log = (
        "==>  Preparing: select * from user where id = ? and name = ?\n"
        "==> Parameters: 1(Long)\n"
    )
    result = CliRunner().invoke(cli, ["db", "mybatis-sql", "--strict"], input=log)
    assert result.exit_code != 0


def test_format_replace_with_total():
    log = (
        "before\n"
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "<==      Total: 1\n"
        "after\n"
    )
    result, warns = format_mybatis_log(log)
    assert "before" in result
    assert "after" in result
    assert "select * from user where id = 1;" in result
    assert "Preparing:" not in result
    assert "Parameters:" not in result
    assert "Total:" not in result
    assert warns == []


def test_format_append_with_total():
    log = (
        "before\n"
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "<==      Total: 1\n"
        "after\n"
    )
    result, warns = format_mybatis_log(log, mode="append")
    assert "before" in result
    assert "after" in result
    assert "Preparing:" in result
    assert "Parameters:" in result
    assert "Total:" in result
    assert "-- Formatted SQL:" in result
    assert result.index("Total:") < result.index("-- Formatted SQL:")
    assert "select * from user where id = 1;" in result
    assert warns == []


def test_format_replace_with_total_prefix():
    log = (
        "before\n"
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "2026-06-21 DEBUG <==      Total: 1\n"
        "after\n"
    )
    result, warns = format_mybatis_log(log)
    assert "select * from user where id = 1;" in result
    assert "Total:" not in result
    assert warns == []


def test_format_no_total_preserves_existing_behavior():
    log = (
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
    )
    result, warns = format_mybatis_log(log)
    assert "select * from user where id = 1;" in result
    assert warns == []


def test_format_normal_line_between_params_and_next_preparing():
    log = (
        "==>  Preparing: select * from user where id = ?\n"
        "==> Parameters: 1(Long)\n"
        "some normal log\n"
        "==>  Preparing: select * from order where id = ?\n"
        "==> Parameters: 2(Long)\n"
    )
    result, warns = format_mybatis_log(log)
    assert "select * from user where id = 1;" in result
    assert "select * from order where id = 2;" in result
    assert "some normal log" in result
    assert warns == []


def test_cli_db_help_includes_mybatis_sql():
    result = CliRunner().invoke(cli, ["db", "--help"])
    assert result.exit_code == 0
    assert "mybatis-sql" in result.output
