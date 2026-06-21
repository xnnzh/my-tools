from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.db.insert_sql_csv import (
    InsertCsvData,
    parse_columns,
    parse_insert_sql,
    parse_sql_literal,
    write_csv,
)


def test_parse_columns_basic():
    assert parse_columns("(id, name, age)") == ["id", "name", "age"]


def test_parse_columns_backtick():
    assert parse_columns("(`id`, `user_name`)") == ["id", "user_name"]


def test_parse_columns_single():
    assert parse_columns("(id)") == ["id"]


def test_parse_sql_literal_null():
    assert parse_sql_literal("NULL") is None
    assert parse_sql_literal("null") is None


def test_parse_sql_literal_string():
    assert parse_sql_literal("'Alice'") == "Alice"


def test_parse_sql_literal_escaped_quote():
    assert parse_sql_literal("'O''Brien'") == "O'Brien"


def test_parse_sql_literal_number():
    assert parse_sql_literal("123") == "123"
    assert parse_sql_literal("12.34") == "12.34"


def test_parse_sql_literal_boolean():
    assert parse_sql_literal("true") == "true"
    assert parse_sql_literal("TRUE") == "TRUE"


def test_parse_sql_literal_function():
    assert parse_sql_literal("now()") == "now()"


def test_parse_sql_literal_empty():
    assert parse_sql_literal("") is None


def test_basic_single_row():
    data = parse_insert_sql(
        "insert into table1 (id, name, age) values (1, 'Alice', 18);"
    )
    assert data.columns == ["id", "name", "age"]
    assert data.rows == [["1", "Alice", "18"]]
    assert data.warnings == []


def test_multi_row():
    data = parse_insert_sql(
        "insert into table1 (id, name)\nvalues (1, 'Alice'), (2, 'Bob');"
    )
    assert data.columns == ["id", "name"]
    assert data.rows == [["1", "Alice"], ["2", "Bob"]]
    assert data.warnings == []


def test_backtick_columns():
    data = parse_insert_sql(
        "insert into `table1` (`id`, `user_name`) values (1, 'Alice');"
    )
    assert data.columns == ["id", "user_name"]
    assert data.rows == [["1", "Alice"]]


def test_schema_table():
    data = parse_insert_sql(
        "insert into `db1`.`table1` (`id`, `name`) values (1, 'Alice');"
    )
    assert data.columns == ["id", "name"]
    assert data.rows == [["1", "Alice"]]


def test_string_with_comma():
    data = parse_insert_sql(
        "insert into table1 (id, name) values (1, 'Alice,Bob');"
    )
    assert data.rows == [["1", "Alice,Bob"]]


def test_escaped_quote_in_value():
    data = parse_insert_sql(
        "insert into table1 (id, name) values (1, 'O''Brien');"
    )
    assert data.rows == [["1", "O'Brien"]]


def test_null_value():
    data = parse_insert_sql(
        "insert into table1 (id, deleted_at) values (1, NULL);"
    )
    assert data.rows == [["1", None]]


def test_function_expression():
    data = parse_insert_sql(
        "insert into table1 (id, created_at) values (1, now());"
    )
    assert data.rows == [["1", "now()"]]


def test_boolean_and_number():
    data = parse_insert_sql(
        "insert into table1 (id, active, created_at) "
        "values (1, true, '2026-06-21 10:00:00');"
    )
    assert data.rows == [["1", "true", "2026-06-21 10:00:00"]]


def test_fewer_values_non_strict():
    data = parse_insert_sql(
        "insert into table1 (id, name, age) values (1, 'Alice');"
    )
    assert data.rows == [["1", "Alice", None]]
    assert data.warnings != []


def test_fewer_values_strict():
    try:
        parse_insert_sql(
            "insert into table1 (id, name, age) values (1, 'Alice');",
            strict=True,
        )
        assert False, "should have raised"
    except ValueError:
        pass


def test_more_values_non_strict():
    data = parse_insert_sql(
        "insert into table1 (id, name) values (1, 'Alice', 18);"
    )
    assert data.rows == [["1", "Alice"]]
    assert data.warnings != []


def test_more_values_strict():
    try:
        parse_insert_sql(
            "insert into table1 (id, name) values (1, 'Alice', 18);",
            strict=True,
        )
        assert False, "should have raised"
    except ValueError:
        pass


def test_missing_column_list():
    try:
        parse_insert_sql("insert into table1 values (1, 'Alice');")
        assert False, "should have raised"
    except ValueError as e:
        assert "列名" in str(e)


def test_insert_select_not_supported():
    try:
        parse_insert_sql(
            "insert into table1 (id, name) select id, name from table2;"
        )
        assert False, "should have raised"
    except ValueError as e:
        assert "INSERT" in str(e) and "SELECT" in str(e)


def test_missing_values():
    try:
        parse_insert_sql("insert into table1 (id, name) (1, 'Alice');")
        assert False, "should have raised"
    except ValueError as e:
        assert "VALUES" in str(e)


def test_write_csv(tmp_path):
    csv_file = tmp_path / "out.csv"
    data = InsertCsvData(
        columns=["id", "name"],
        rows=[["1", "Alice"], ["2", "Bob"]],
    )
    with open(csv_file, "w", newline="") as f:
        write_csv(data, f)
    content = csv_file.read_text()
    assert "id,name" in content
    assert "1,Alice" in content
    assert "2,Bob" in content


def test_write_csv_with_none(tmp_path):
    csv_file = tmp_path / "out.csv"
    data = InsertCsvData(
        columns=["id", "name", "age"],
        rows=[["1", "Alice", None]],
    )
    with open(csv_file, "w", newline="") as f:
        write_csv(data, f)
    content = csv_file.read_text()
    assert "id,name,age" in content
    assert "1,Alice," in content


def test_cli_help():
    result = CliRunner().invoke(cli, ["db", "insert-sql-to-csv", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--encoding" in result.output
    assert "--delimiter" in result.output
    assert "--strict" in result.output


def test_cli_stdin():
    result = CliRunner().invoke(
        cli,
        ["db", "insert-sql-to-csv"],
        input="insert into table1 (id, name) values (1, 'Alice');",
    )
    assert result.exit_code == 0
    assert "id,name" in result.output
    assert "1,Alice" in result.output


def test_cli_file_input(tmp_path):
    sql_file = tmp_path / "insert.sql"
    sql_file.write_text(
        "insert into table1 (id, name) values (1, 'Alice'), (2, 'Bob');"
    )
    result = CliRunner().invoke(cli, ["db", "insert-sql-to-csv", str(sql_file)])
    assert result.exit_code == 0
    assert "id,name" in result.output
    assert "1,Alice" in result.output
    assert "2,Bob" in result.output


def test_cli_output_file(tmp_path):
    sql_file = tmp_path / "insert.sql"
    csv_file = tmp_path / "out.csv"
    sql_file.write_text(
        "insert into table1 (id, name) values (1, 'Alice');"
    )
    result = CliRunner().invoke(
        cli,
        ["db", "insert-sql-to-csv", str(sql_file), "-o", str(csv_file)],
    )
    assert result.exit_code == 0
    assert csv_file.exists()
    content = csv_file.read_text()
    assert "id,name" in content
    assert "1,Alice" in content


def test_cli_strict_fails():
    result = CliRunner().invoke(
        cli,
        ["db", "insert-sql-to-csv", "--strict"],
        input="insert into table1 (id, name) values (1);",
    )
    assert result.exit_code != 0


def test_cli_db_help_includes():
    result = CliRunner().invoke(cli, ["db", "--help"])
    assert result.exit_code == 0
    assert "insert-sql-to-csv" in result.output
