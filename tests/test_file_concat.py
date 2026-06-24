from pathlib import Path

from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.file.concat import (
    collect_files,
    concatenate_files,
    read_file_content,
    sort_files,
)


def test_collect_files_single_file(tmp_path: Path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    result = collect_files(str(f))
    assert result == [f]


def test_collect_files_dir_flat(tmp_path: Path):
    (tmp_path / "b.txt").write_text("b")
    (tmp_path / "a.txt").write_text("a")
    result = collect_files(str(tmp_path))
    assert len(result) == 2
    assert result[0].name == "a.txt"
    assert result[1].name == "b.txt"


def test_collect_files_skip_hidden(tmp_path: Path):
    (tmp_path / "visible.txt").write_text("visible")
    (tmp_path / ".hidden.txt").write_text("hidden")
    result = collect_files(str(tmp_path))
    names = [f.name for f in result]
    assert "visible.txt" in names
    assert ".hidden.txt" not in names


def test_collect_files_no_skip_hidden(tmp_path: Path):
    (tmp_path / "visible.txt").write_text("visible")
    (tmp_path / ".hidden.txt").write_text("hidden")
    result = collect_files(str(tmp_path), skip_hidden=False)
    names = [f.name for f in result]
    assert "visible.txt" in names
    assert ".hidden.txt" in names


def test_collect_files_filter_extensions(tmp_path: Path):
    (tmp_path / "a.txt").write_text("text")
    (tmp_path / "b.md").write_text("markdown")
    (tmp_path / "c.log").write_text("log")
    result = collect_files(str(tmp_path), extensions=(".txt", ".md"))
    names = [f.name for f in result]
    assert "a.txt" in names
    assert "b.md" in names
    assert "c.log" not in names


def test_collect_files_skips_directories(tmp_path: Path):
    (tmp_path / "a.txt").write_text("text")
    (tmp_path / "sub").mkdir()
    result = collect_files(str(tmp_path))
    assert len(result) == 1


def test_sort_files_by_name_length_then_lexicographic(tmp_path: Path):
    files = []
    for name in ["z.txt", "a.txt", "ab.txt", "aa.txt", "abc.txt"]:
        f = tmp_path / name
        f.write_text(name)
        files.append(f)

    sorted_files = sort_files(files)
    sorted_names = [f.name for f in sorted_files]
    assert sorted_names == ["a.txt", "z.txt", "aa.txt", "ab.txt", "abc.txt"]


def test_read_file_content(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    result = read_file_content(f, encoding="utf-8", skip_empty=False)
    assert result == "hello world"


def test_read_file_content_skip_empty_skips(tmp_path: Path):
    f = tmp_path / "empty.txt"
    f.write_text("")
    result = read_file_content(f, encoding="utf-8", skip_empty=True)
    assert result is None


def test_read_file_content_skip_empty_blank_skips(tmp_path: Path):
    f = tmp_path / "blank.txt"
    f.write_text("   \n\n  ")
    result = read_file_content(f, encoding="utf-8", skip_empty=True)
    assert result is None


def test_read_file_content_skip_empty_non_empty(tmp_path: Path):
    f = tmp_path / "nonempty.txt"
    f.write_text("  data  ")
    result = read_file_content(f, encoding="utf-8", skip_empty=True)
    assert result == "  data  "


def test_concatenate_files_basic(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello\n")
    b.write_text("world\n")
    result = concatenate_files([str(a), str(b)])
    assert result == "hello\nworld\n"


def test_concatenate_files_with_separator(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello")
    b.write_text("world")
    result = concatenate_files([str(a), str(b)], separator="\n---\n")
    assert result == "hello\n---\nworld"


def test_concatenate_files_dir(tmp_path: Path):
    d = tmp_path / "logs"
    d.mkdir()
    (d / "z.txt").write_text("z")
    (d / "a.txt").write_text("a")
    result = concatenate_files([str(d)])
    assert result == "az"


def test_concatenate_files_skip_empty(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello")
    b.write_text("")
    result = concatenate_files([str(a), str(b)], skip_empty=True)
    assert result == "hello"


def test_concatenate_files_skip_hidden(tmp_path: Path):
    a = tmp_path / "visible.txt"
    b = tmp_path / ".hidden.txt"
    a.write_text("hello")
    b.write_text("secret")
    result = concatenate_files([str(tmp_path)])
    assert result == "hello"


def test_concatenate_files_no_skip_hidden(tmp_path: Path):
    a = tmp_path / "visible.txt"
    b = tmp_path / ".hidden.txt"
    a.write_text("hello")
    b.write_text("secret")
    result = concatenate_files([str(tmp_path)], skip_hidden=False)
    assert "hello" in result
    assert "secret" in result


def test_concatenate_files_filter_extensions(tmp_path: Path):
    (tmp_path / "a.txt").write_text("text")
    (tmp_path / "b.md").write_text("markdown")
    result = concatenate_files([str(tmp_path)], extensions=(".md",))
    assert result == "markdown"


def test_concatenate_files_file_not_found(tmp_path: Path):
    import pytest
    with pytest.raises(FileNotFoundError):
        concatenate_files([str(tmp_path / "nope.txt")])


def test_cli_help():
    result = CliRunner().invoke(cli, ["file", "concat", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--encoding" in result.output
    assert "--separator" in result.output
    assert "--skip-empty" in result.output
    assert "--skip-hidden" in result.output
    assert "--ext" in result.output


def test_cli_file_command_listed():
    result = CliRunner().invoke(cli, ["file", "--help"])
    assert result.exit_code == 0
    assert "concat" in result.output


def test_cli_basic_concat(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello\n")
    b.write_text("world\n")
    result = CliRunner().invoke(
        cli, ["file", "concat", str(a), str(b)]
    )
    assert result.exit_code == 0
    assert "hello\nworld" in result.output


def test_cli_output_file(tmp_path: Path):
    a = tmp_path / "a.txt"
    out = tmp_path / "out.txt"
    a.write_text("hello")
    result = CliRunner().invoke(
        cli, ["file", "concat", str(a), "-o", str(out)]
    )
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8") == "hello"


def test_cli_separator(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello")
    b.write_text("world")
    result = CliRunner().invoke(
        cli, ["file", "concat", str(a), str(b), "--separator", "\n---\n"]
    )
    assert result.exit_code == 0
    assert "hello\n---\nworld" in result.output


def test_cli_skip_empty(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello")
    b.write_text("")
    result = CliRunner().invoke(
        cli, ["file", "concat", str(a), str(b), "--skip-empty"]
    )
    assert result.exit_code == 0
    assert result.output.strip() == "hello"


def test_cli_extensions(tmp_path: Path):
    (tmp_path / "a.txt").write_text("text")
    (tmp_path / "b.md").write_text("markdown")
    result = CliRunner().invoke(
        cli, ["file", "concat", str(tmp_path), "--ext", ".txt"]
    )
    assert result.exit_code == 0
    assert result.output.strip() == "text"


def test_cli_dir_collects_and_sorts(tmp_path: Path):
    d = tmp_path / "logs"
    d.mkdir()
    (d / "zz.txt").write_text("zz")
    (d / "a.txt").write_text("a")
    (d / "aaa.txt").write_text("aaa")
    result = CliRunner().invoke(cli, ["file", "concat", str(d)])
    assert result.exit_code == 0
    assert result.output.strip() == "azzaaa"


def test_cli_missing_path_fails(tmp_path: Path):
    result = CliRunner().invoke(
        cli, ["file", "concat", str(tmp_path / "nope")]
    )
    assert result.exit_code != 0
