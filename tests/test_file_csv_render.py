from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.file.csv_render import (
    convert_csv,
    extract_template_fields,
    render_template,
)


def test_extract_template_fields():
    fields = extract_template_fields("{name} is {age}")
    assert fields == {"name", "age"}


def test_extract_template_fields_special_chars():
    fields = extract_template_fields(
        "{@timestamp} [{__tag__:_pod_name_}] {message}"
    )
    assert fields == {"@timestamp", "__tag__:_pod_name_", "message"}


def test_render_template_basic():
    row = {"name": "Alice", "age": "18"}
    result, warns = render_template("{name} is {age}", row)
    assert result == "Alice is 18"
    assert warns == []


def test_render_template_missing_field_non_strict():
    row = {"name": "Alice"}
    result, warns = render_template("{name} {missing}", row)
    assert result == "Alice "
    assert warns != []


def test_render_template_missing_field_strict():
    row = {"name": "Alice"}
    try:
        render_template("{name} {missing}", row, strict=True)
        assert False, "should have raised"
    except ValueError:
        pass


def test_convert_csv_basic():
    result = convert_csv(
        "name,age\nAlice,18\nBob,20\n",
        template="{name} is {age}",
    )
    assert result.lines == ["Alice is 18", "Bob is 20"]
    assert result.warnings == []


def test_convert_csv_default_template():
    csv_text = (
        "@timestamp,level,logger_name,message,thread_name\n"
        "2026-06-15T14:01:44.051740311+08:00,DEBUG,com.xxx.Mapper,"
        "==>  Preparing: select * from user where id = ?,context-aware-task-2\n"
    )
    result = convert_csv(csv_text)
    assert len(result.lines) == 1
    line = result.lines[0]
    assert "2026-06-15T14:01:44.051740311+08:00" in line
    assert "DEBUG" in line
    assert "context-aware-task-2" in line
    assert "com.xxx.Mapper" in line
    assert "==>  Preparing:" in line
    assert result.warnings == []


def test_convert_csv_special_chars_in_headers():
    csv_text = "@timestamp,__tag__:_pod_name_,message\nt,pod-1,msg\n"
    result = convert_csv(
        csv_text,
        template="{@timestamp} [{__tag__:_pod_name_}] {message}",
    )
    assert result.lines == ["t [pod-1] msg"]
    assert result.warnings == []


def test_convert_csv_field_with_comma():
    csv_text = 'name,message\nAlice,"hello, world"\n'
    result = convert_csv(csv_text, template="{name}: {message}")
    assert result.lines == ["Alice: hello, world"]
    assert result.warnings == []


def test_convert_csv_field_with_quotes():
    csv_text = 'message\n"hello ""world"""\n'
    result = convert_csv(csv_text, template="{message}")
    assert result.lines == ['hello "world"']
    assert result.warnings == []


def test_convert_csv_field_with_newline():
    csv_text = (
        'level,message\n'
        'ERROR,"java.lang.RuntimeException: xxx\n'
        '    at com.xxx.Service.run(Service.java:1)"\n'
    )
    result = convert_csv(csv_text, template="{level} - {message}")
    assert len(result.lines) == 1
    assert "ERROR" in result.lines[0]
    assert "java.lang.RuntimeException" in result.lines[0]
    assert "\n" in result.lines[0]
    assert result.warnings == []


def test_convert_csv_missing_field_non_strict():
    csv_text = "name\nAlice\n"
    result = convert_csv(csv_text, template="{name} {missing}")
    assert result.lines == ["Alice "]
    assert result.warnings != []
    assert any("missing" in w for w in result.warnings)


def test_convert_csv_missing_field_strict():
    csv_text = "name\nAlice\n"
    try:
        convert_csv(csv_text, template="{name} {missing}", strict=True)
        assert False, "should have raised"
    except ValueError:
        pass


def test_convert_csv_empty():
    try:
        convert_csv("")
        assert False, "should have raised"
    except ValueError as e:
        assert "空" in str(e)


def test_convert_csv_bom_header():
    csv_text = "\ufeff@timestamp,message\nt,hello\n"
    result = convert_csv(csv_text, template="{@timestamp} {message}")
    assert result.lines == ["t hello"]
    assert result.warnings == []


def test_convert_csv_header_only():
    result = convert_csv("name,age\n", template="{name}")
    assert result.lines == []
    assert result.warnings == []


def test_cli_help():
    result = CliRunner().invoke(cli, ["file", "csv-render", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--encoding" in result.output
    assert "--format" in result.output
    assert "--strict" in result.output


def test_cli_stdin():
    result = CliRunner().invoke(
        cli,
        ["file", "csv-render", "--format", "{name} is {age}"],
        input="name,age\nAlice,18\n",
    )
    assert result.exit_code == 0
    assert "Alice is 18" in result.output


def test_cli_file_input(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,age\nAlice,18\n")
    result = CliRunner().invoke(
        cli,
        ["file", "csv-render", str(csv_file), "--format", "{name}"],
    )
    assert result.exit_code == 0
    assert "Alice" in result.output


def test_cli_output_file(tmp_path):
    csv_file = tmp_path / "test.csv"
    out_file = tmp_path / "out.txt"
    csv_file.write_text("name,age\nAlice,18\n")
    result = CliRunner().invoke(
        cli,
        [
            "file", "csv-render", str(csv_file),
            "--format", "{name} is {age}",
            "-o", str(out_file),
        ],
    )
    assert result.exit_code == 0
    assert out_file.read_text() == "Alice is 18\n"


def test_cli_default_template():
    csv_text = (
        "@timestamp,level,logger_name,message,thread_name\n"
        "2026-06-15T14:01:44.051740311+08:00,DEBUG,com.xxx.Mapper,"
        "==>  Preparing: select * from user where id = ?,context-aware-task-2\n"
    )
    result = CliRunner().invoke(cli, ["file", "csv-render"], input=csv_text)
    assert result.exit_code == 0
    assert "2026-06-15T14:01:44.051740311+08:00" in result.output
    assert "DEBUG" in result.output
    assert "context-aware-task-2" in result.output
    assert "==>  Preparing:" in result.output


def test_cli_strict_fails():
    result = CliRunner().invoke(
        cli,
        ["file", "csv-render", "--format", "{missing}", "--strict"],
        input="name\nAlice\n",
    )
    assert result.exit_code != 0
