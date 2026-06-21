from pathlib import Path

import pytest
from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.db.csv_insert_sql import (
    ExtraField,
    convert_csv_to_insert_sql,
    merge_field_types,
    parse_extra_assignment,
    parse_field_list,
    parse_field_types,
    quote_identifier,
    quote_table,
    sql_literal,
)


class TestParseFieldList:
    def test_basic(self):
        assert parse_field_list("id,name,age") == ["id", "name", "age"]

    def test_none(self):
        assert parse_field_list(None) is None

    def test_empty(self):
        assert parse_field_list("") == []

    def test_whitespace(self):
        assert parse_field_list(" id , name ") == ["id", "name"]


class TestParseExtraAssignment:
    def test_basic(self):
        ef = parse_extra_assignment("created_by=admin")
        assert ef.name == "created_by"
        assert ef.value == "admin"
        assert ef.raw_sql is False

    def test_value_contains_eq(self):
        ef = parse_extra_assignment("expr=a=b")
        assert ef.name == "expr"
        assert ef.value == "a=b"

    def test_raw_sql(self):
        ef = parse_extra_assignment("x=now()", raw_sql=True)
        assert ef.name == "x"
        assert ef.value == "now()"
        assert ef.raw_sql is True

    def test_missing_eq_raises(self):
        with pytest.raises(ValueError, match="缺少 '='"):
            parse_extra_assignment("justname")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="字段名不能为空"):
            parse_extra_assignment("=value")


class TestParseFieldTypes:
    def test_basic(self):
        assert parse_field_types("id:number,enabled:boolean") == {
            "id": "number",
            "enabled": "boolean",
        }

    def test_none(self):
        assert parse_field_types(None) == {}

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="不支持"):
            parse_field_types("x:unknown")

    def test_conflict_raises(self):
        with pytest.raises(ValueError, match="类型冲突"):
            parse_field_types("x:number,x:boolean")


class TestMergeFieldTypes:
    def test_empty(self):
        assert merge_field_types() == {}

    def test_number_fields(self):
        result = merge_field_types(number_fields=["id", "age"])
        assert result == {"id": "number", "age": "number"}

    def test_boolean_fields(self):
        result = merge_field_types(boolean_fields=["enabled"])
        assert result == {"enabled": "boolean"}

    def test_conflict_number_raises(self):
        with pytest.raises(ValueError, match="类型冲突"):
            merge_field_types(
                field_types={"id": "boolean"}, number_fields=["id"]
            )

    def test_conflict_boolean_raises(self):
        with pytest.raises(ValueError, match="类型冲突"):
            merge_field_types(
                field_types={"id": "number"}, boolean_fields=["id"]
            )

    def test_extra_field_string(self):
        result = merge_field_types(
            extra_fields=[ExtraField("name", "x")]
        )
        assert result == {"name": "string"}

    def test_extra_field_sql(self):
        result = merge_field_types(
            extra_fields=[ExtraField("x", "now()", raw_sql=True)]
        )
        assert result == {"x": "sql"}


class TestQuoteIdentifier:
    def test_basic(self):
        assert quote_identifier("user") == "`user`"

    def test_backtick_escaped(self):
        assert quote_identifier("a`b") == "`a``b`"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            quote_identifier("")


class TestQuoteTable:
    def test_no_database(self):
        assert quote_table(None, "user") == "`user`"

    def test_with_database(self):
        assert quote_table("app", "user") == "`app`.`user`"

    def test_dot_in_table_raises(self):
        with pytest.raises(ValueError, match="不能包含"):
            quote_table(None, "db.table")

    def test_empty_table_raises(self):
        with pytest.raises(ValueError, match="不能为空"):
            quote_table(None, "")


class TestSqlLiteral:
    def test_none(self):
        assert sql_literal(None) == "NULL"

    def test_empty(self):
        assert sql_literal("") == "NULL"

    def test_string(self):
        assert sql_literal("Alice") == "'Alice'"

    def test_string_quote_escaped(self):
        assert sql_literal("O'Brien") == "'O''Brien'"

    def test_string_backslash_escaped(self):
        assert sql_literal(r"C:\tmp") == r"'C:\\tmp'"

    def test_number(self):
        assert sql_literal("123", field_type="number") == "123"

    def test_number_negative(self):
        assert sql_literal("-1", field_type="number") == "-1"

    def test_number_float(self):
        assert sql_literal("3.14", field_type="number") == "3.14"

    def test_number_invalid_raises(self):
        with pytest.raises(ValueError, match="非法数字"):
            sql_literal("abc", field_type="number")

    def test_boolean_true(self):
        assert sql_literal("true", field_type="boolean") == "TRUE"

    def test_boolean_false(self):
        assert sql_literal("FALSE", field_type="boolean") == "FALSE"

    def test_boolean_1(self):
        assert sql_literal("1", field_type="boolean") == "TRUE"

    def test_boolean_0(self):
        assert sql_literal("0", field_type="boolean") == "FALSE"

    def test_boolean_yes(self):
        assert sql_literal("yes", field_type="boolean") == "TRUE"

    def test_boolean_no(self):
        assert sql_literal("no", field_type="boolean") == "FALSE"

    def test_boolean_invalid_raises(self):
        with pytest.raises(ValueError, match="无法识别"):
            sql_literal("maybe", field_type="boolean")

    def test_sql(self):
        assert sql_literal("now()", field_type="sql") == "now()"

    def test_null_type(self):
        assert sql_literal("anything", field_type="null") == "NULL"

    def test_nul_char_raises(self):
        with pytest.raises(ValueError, match="NUL"):
            sql_literal("a\x00b", field_type="string")


class TestConvertCsvToInsertSql:
    def test_basic(self):
        result = convert_csv_to_insert_sql(
            "id,name\n1,Alice\n2,Bob\n", table="user"
        )
        expected = (
            "INSERT INTO `user` (`id`, `name`)\n"
            "VALUES\n"
            "  ('1', 'Alice'),\n"
            "  ('2', 'Bob');\n"
        )
        assert result.sql == expected

    def test_with_database(self):
        result = convert_csv_to_insert_sql(
            "id,name\n1,Alice\n", table="user", database="app"
        )
        assert "`app`.`user`" in result.sql

    def test_fields_white_list(self):
        result = convert_csv_to_insert_sql(
            "id,name,age\n1,Alice,18\n", table="user", fields=["name", "id"]
        )
        assert "`name`, `id`" in result.sql
        assert "'Alice'" in result.sql
        assert "'1'" in result.sql

    def test_exclude_fields(self):
        result = convert_csv_to_insert_sql(
            "id,name,age,password\n1,Alice,18,secret\n",
            table="user",
            exclude_fields=["password"],
        )
        assert "password" not in result.sql
        assert "`id`, `name`, `age`" in result.sql

    def test_fields_and_exclude_mutually_exclusive(self):
        with pytest.raises(ValueError, match="不能同时指定"):
            convert_csv_to_insert_sql(
                "id,name\n1,Alice\n",
                table="user",
                fields=["id"],
                exclude_fields=["name"],
            )

    def test_field_not_exists_raises(self):
        with pytest.raises(ValueError, match="不存在于 CSV"):
            convert_csv_to_insert_sql(
                "id,name\n1,Alice\n", table="user", fields=["nonexistent"]
            )

    def test_exclude_field_not_exists_non_strict(self):
        result = convert_csv_to_insert_sql(
            "id,name\n1,Alice\n",
            table="user",
            exclude_fields=["nonexistent"],
            strict=False,
        )
        assert "nonexistent" in result.warnings[0]

    def test_exclude_field_not_exists_strict_raises(self):
        with pytest.raises(ValueError, match="不存在于 CSV"):
            convert_csv_to_insert_sql(
                "id,name\n1,Alice\n",
                table="user",
                exclude_fields=["nonexistent"],
                strict=True,
            )

    def test_extra_field(self):
        result = convert_csv_to_insert_sql(
            "id,name\n1,Alice\n",
            table="user",
            extra_fields=[ExtraField("created_by", "admin")],
        )
        assert "'admin'" in result.sql

    def test_extra_sql_field(self):
        result = convert_csv_to_insert_sql(
            "id,name\n1,Alice\n",
            table="user",
            extra_fields=[ExtraField("created_at", "now()", raw_sql=True)],
        )
        assert "now()" in result.sql
        assert "'now()'" not in result.sql

    def test_extra_conflict_with_csv(self):
        with pytest.raises(ValueError, match="重名"):
            convert_csv_to_insert_sql(
                "id,name\n1,Alice\n",
                table="user",
                extra_fields=[ExtraField("id", "x")],
            )

    def test_extra_self_conflict(self):
        with pytest.raises(ValueError, match="重名"):
            convert_csv_to_insert_sql(
                "id,name\n1,Alice\n",
                table="user",
                extra_fields=[
                    ExtraField("x", "a"),
                    ExtraField("x", "b"),
                ],
            )

    def test_empty_cell_null(self):
        result = convert_csv_to_insert_sql(
            "id,name\n1,\n", table="user"
        )
        assert "NULL" in result.sql
        assert "''" not in result.sql

    def test_text_null_not_converted(self):
        result = convert_csv_to_insert_sql(
            "id,name\n1,NULL\n", table="user"
        )
        assert "'NULL'" in result.sql
        assert "NULL" in result.sql.split("VALUES")[1].strip()

    def test_number_field(self):
        result = convert_csv_to_insert_sql(
            "id,name,age\n1,Alice,18\n",
            table="user",
            field_types={"id": "number", "age": "number"},
        )
        assert "(1, 'Alice', 18)" in result.sql

    def test_boolean_field(self):
        result = convert_csv_to_insert_sql(
            "id,name,enabled\n1,Alice,true\n",
            table="user",
            field_types={"enabled": "boolean"},
        )
        assert "TRUE" in result.sql

    def test_sql_field(self):
        result = convert_csv_to_insert_sql(
            "id,created_at\n1,now()\n",
            table="user",
            field_types={"created_at": "sql"},
        )
        assert "now()" in result.sql

    def test_number_fields_shortcut(self):
        result = convert_csv_to_insert_sql(
            "id,name,age\n1,Alice,18\n",
            table="user",
            field_types={"id": "number", "age": "number"},
        )
        assert "(1, 'Alice', 18)" in result.sql

    def test_csv_with_quotes_and_commas(self):
        result = convert_csv_to_insert_sql(
            'id,desc\n1,"a,b,c"\n', table="user"
        )
        assert "'a,b,c'" in result.sql

    def test_batch_size(self):
        rows = "\n".join([f"{i},name{i}" for i in range(5)])
        result = convert_csv_to_insert_sql(
            f"id,name\n{rows}\n", table="user", batch_size=2
        )
        count = result.sql.count("INSERT INTO")
        assert count == 3

    def test_no_batch(self):
        rows = "\n".join([f"{i},name{i}" for i in range(3)])
        result = convert_csv_to_insert_sql(
            f"id,name\n{rows}\n", table="user", batch=False
        )
        count = result.sql.count("INSERT INTO")
        assert count == 3

    def test_empty_csv_raises(self):
        with pytest.raises(ValueError, match="CSV 内容为空"):
            convert_csv_to_insert_sql("", table="user")

    def test_headers_only(self):
        result = convert_csv_to_insert_sql(
            "id,name\n", table="user"
        )
        assert result.sql == ""

    def test_bom_header(self):
        result = convert_csv_to_insert_sql(
            "\ufeffid,name\n1,Alice\n", table="user"
        )
        assert "(`id`, `name`)" in result.sql

    def test_type_declared_field_not_in_output(self):
        with pytest.raises(ValueError, match="不存在于最终输出列"):
            convert_csv_to_insert_sql(
                "id,name\n1,Alice\n",
                table="user",
                field_types={"nonexistent": "number"},
            )

    def test_nul_in_string_raises(self):
        with pytest.raises(ValueError, match="NUL"):
            convert_csv_to_insert_sql(
                "id,val\n1,a\x00b\n", table="user"
            )

    def test_batch_size_zero_raises(self):
        with pytest.raises(ValueError, match="必须为正整数"):
            convert_csv_to_insert_sql(
                "id,name\n1,Alice\n", table="user", batch_size=0
            )

    def test_warning_preserved(self):
        result = convert_csv_to_insert_sql(
            "id,name\n1,Alice\n",
            table="user",
            exclude_fields=["nonexistent"],
        )
        assert len(result.warnings) == 1


class TestCli:
    def test_help(self):
        result = CliRunner().invoke(cli, ["db", "csv-to-insert-sql", "--help"])
        assert result.exit_code == 0
        assert "--table" in result.output
        assert "--database" in result.output
        assert "--fields" in result.output
        assert "--exclude-fields" in result.output
        assert "--extra" in result.output
        assert "--extra-sql" in result.output
        assert "--field-types" in result.output
        assert "--number-fields" in result.output
        assert "--boolean-fields" in result.output
        assert "--batch-size" in result.output
        assert "--no-batch" in result.output
        assert "--output" in result.output
        assert "--encoding" in result.output
        assert "--strict" in result.output

    def test_stdin(self):
        result = CliRunner().invoke(
            cli, ["db", "csv-to-insert-sql", "--table", "user"],
            input="id,name\n1,Alice\n",
        )
        assert result.exit_code == 0
        assert "INSERT INTO `user`" in result.output
        assert "('1', 'Alice')" in result.output

    def test_file_input(self, tmp_path: Path):
        f = tmp_path / "data.csv"
        f.write_text("id,name\n1,Alice\n", encoding="utf-8")
        out = tmp_path / "out.sql"
        result = CliRunner().invoke(
            cli, ["db", "csv-to-insert-sql", str(f), "--table", "user", "-o", str(out)]
        )
        assert result.exit_code == 0
        content = out.read_text(encoding="utf-8")
        assert "INSERT INTO `user`" in content

    def test_missing_table_fails(self):
        result = CliRunner().invoke(
            cli, ["db", "csv-to-insert-sql"], input="id,name\n1,Alice\n"
        )
        assert result.exit_code != 0

    def test_number_fields(self):
        result = CliRunner().invoke(
            cli, ["db", "csv-to-insert-sql", "--table", "user", "--number-fields", "id"],
            input="id,name\n1,Alice\n",
        )
        assert result.exit_code == 0
        assert "(1, 'Alice')" in result.output

    def test_number_fields_comma_separated(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--number-fields", "id,age"],
            input="id,name,age\n1,Alice,18\n",
        )
        assert result.exit_code == 0
        assert "(1, 'Alice', 18)" in result.output

    def test_boolean_fields(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--boolean-fields", "enabled"],
            input="id,name,enabled\n1,Alice,true\n",
        )
        assert result.exit_code == 0
        assert "TRUE" in result.output

    def test_boolean_fields_comma_separated(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user",
             "--boolean-fields", "enabled,deleted"],
            input="id,name,enabled,deleted\n1,Alice,true,false\n",
        )
        assert result.exit_code == 0
        assert "('1', 'Alice', TRUE, FALSE)" in result.output

    def test_number_boolean_mixed_multiple_use(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user",
             "--number-fields", "id", "--number-fields", "age",
             "--boolean-fields", "enabled,deleted"],
            input="id,name,age,enabled,deleted\n1,Alice,18,true,false\n",
        )
        assert result.exit_code == 0
        assert "(1, 'Alice', 18, TRUE, FALSE)" in result.output

    def test_extra(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--extra", "created_by=admin"],
            input="id,name\n1,Alice\n",
        )
        assert result.exit_code == 0
        assert "'admin'" in result.output

    def test_extra_sql(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--extra-sql", "created_at=now()"],
            input="id,name\n1,Alice\n",
        )
        assert result.exit_code == 0
        assert "now()" in result.output

    def test_fields(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--fields", "name,id"],
            input="id,name\n1,Alice\n",
        )
        assert result.exit_code == 0
        name_pos = result.output.index("`name`")
        id_pos = result.output.index("`id`")
        assert name_pos < id_pos

    def test_exclude_fields(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--exclude-fields", "password"],
            input="id,name,password\n1,Alice,secret\n",
        )
        assert result.exit_code == 0
        assert "password" not in result.output

    def test_encoding(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--encoding", "gbk"],
            input="id,name\n1,Alice\n",
        )
        assert result.exit_code == 0
        assert "('1', 'Alice')" in result.output

    def test_strict_warning_fails(self):
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user",
             "--exclude-fields", "nonexistent", "--strict"],
            input="id,name\n1,Alice\n",
        )
        assert result.exit_code != 0

    def test_batch_size(self):
        rows = "\n".join([f"{i},n{i}" for i in range(5)])
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--batch-size", "2"],
            input=f"id,name\n{rows}\n",
        )
        assert result.exit_code == 0
        assert result.output.count("INSERT INTO") == 3

    def test_no_batch(self):
        rows = "\n".join([f"{i},n{i}" for i in range(3)])
        result = CliRunner().invoke(
            cli,
            ["db", "csv-to-insert-sql", "--table", "user", "--no-batch"],
            input=f"id,name\n{rows}\n",
        )
        assert result.exit_code == 0
        assert result.output.count("INSERT INTO") == 3
