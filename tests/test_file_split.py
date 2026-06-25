from pathlib import Path

import pytest
from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.file.split import (
    SplitConfig,
    generate_next_suffix,
    parse_size,
    split_file,
)


class TestParseSize:
    def test_plain_number(self):
        assert parse_size("1024") == 1024

    def test_k(self):
        assert parse_size("1K") == 1024

    def test_kib(self):
        assert parse_size("1KiB") == 1024

    def test_kb(self):
        assert parse_size("1KB") == 1000

    def test_m(self):
        assert parse_size("2M") == 2 * 1024 * 1024

    def test_mib(self):
        assert parse_size("2MiB") == 2 * 1024 * 1024

    def test_mb(self):
        assert parse_size("2MB") == 2 * 1000 * 1000

    def test_g(self):
        assert parse_size("1G") == 1024 ** 3

    def test_gb(self):
        assert parse_size("1GB") == 1000 ** 3

    def test_t(self):
        assert parse_size("1T") == 1024 ** 4

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="无法解析大小"):
            parse_size("abc")

    def test_invalid_number_raises(self):
        with pytest.raises(ValueError, match="无法解析大小"):
            parse_size("xK")


class TestGenerateNextSuffix:
    def test_numeric_zero(self):
        assert generate_next_suffix(0, 2, numeric=True) == "00"

    def test_numeric_leading_zero(self):
        assert generate_next_suffix(3, 3, numeric=True) == "003"

    def test_numeric_large(self):
        assert generate_next_suffix(100, 2, numeric=True) == "100"

    def test_alpha_start(self):
        assert generate_next_suffix(0, 2, numeric=False) == "aa"

    def test_alpha_second(self):
        assert generate_next_suffix(1, 2, numeric=False) == "ab"

    def test_alpha_25th(self):
        assert generate_next_suffix(25, 2, numeric=False) == "az"

    def test_alpha_26th(self):
        assert generate_next_suffix(26, 2, numeric=False) == "ba"

    def test_alpha_52th(self):
        assert generate_next_suffix(52, 2, numeric=False) == "ca"

    def test_alpha_single_digit_length(self):
        assert generate_next_suffix(0, 1, numeric=False) == "a"
        assert generate_next_suffix(1, 1, numeric=False) == "b"

    def test_alpha_three_digit_length(self):
        assert generate_next_suffix(0, 3, numeric=False) == "aaa"

    def test_alpha_overflow_length(self):
        result = generate_next_suffix(27, 3, numeric=False)
        assert len(result) == 3
        assert result == "abb"


class TestSplitFileByLines:
    def test_basic_lines_split(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        lines = [f"line{i}" for i in range(100)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "chunk-"),
            lines_per_chunk=30,
        )
        count = split_file(config)
        assert count == 4

        chunk0 = tmp_path / "chunk-aa"
        chunk1 = tmp_path / "chunk-ab"
        chunk2 = tmp_path / "chunk-ac"
        chunk3 = tmp_path / "chunk-ad"
        assert chunk0.exists()
        assert chunk1.exists()
        assert chunk2.exists()
        assert chunk3.exists()

        assert chunk0.read_text(encoding="utf-8") == "\n".join(lines[0:30]) + "\n"
        assert chunk1.read_text(encoding="utf-8") == "\n".join(lines[30:60]) + "\n"
        assert chunk2.read_text(encoding="utf-8") == "\n".join(lines[60:90]) + "\n"
        assert chunk3.read_text(encoding="utf-8") == "\n".join(lines[90:100])

    def test_exact_line_count(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        lines = [f"line{i}" for i in range(50)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "part-"),
            lines_per_chunk=50,
        )
        count = split_file(config)
        assert count == 1
        chunk = tmp_path / "part-aa"
        assert chunk.exists()
        assert chunk.read_text(encoding="utf-8") == "\n".join(lines)

    def test_empty_file(self, tmp_path: Path):
        input_file = tmp_path / "empty.txt"
        input_file.write_text("", encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "empty-"),
            lines_per_chunk=10,
        )
        count = split_file(config)
        assert count == 0
        assert not list(tmp_path.glob("empty-*"))

    def test_single_line(self, tmp_path: Path):
        input_file = tmp_path / "single.txt"
        input_file.write_text("hello", encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "s-"),
            lines_per_chunk=10,
        )
        count = split_file(config)
        assert count == 1
        chunk = tmp_path / "s-aa"
        assert chunk.exists()
        assert chunk.read_text(encoding="utf-8") == "hello"

    def test_numeric_suffix(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        lines = [f"line{i}" for i in range(50)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "n-"),
            lines_per_chunk=20,
            numeric_suffix=True,
        )
        count = split_file(config)
        assert count == 3
        assert (tmp_path / "n-00").exists()
        assert (tmp_path / "n-01").exists()
        assert (tmp_path / "n-02").exists()

    def test_custom_suffix_length(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        lines = [f"line{i}" for i in range(100)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "l-"),
            lines_per_chunk=30,
            suffix_length=3,
        )
        count = split_file(config)
        assert count == 4
        assert (tmp_path / "l-aaa").exists()
        assert (tmp_path / "l-aab").exists()
        assert (tmp_path / "l-aac").exists()
        assert (tmp_path / "l-aad").exists()

    def test_numbering_start(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        lines = [f"line{i}" for i in range(50)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "s-"),
            lines_per_chunk=20,
            numbering_start=3,
            numeric_suffix=True,
        )
        count = split_file(config)
        assert count == 3
        assert (tmp_path / "s-03").exists()
        assert (tmp_path / "s-04").exists()
        assert (tmp_path / "s-05").exists()

    def test_trailing_newline_handling(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        input_file.write_text("a\nb\nc\n", encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "t-"),
            lines_per_chunk=2,
        )
        count = split_file(config)
        assert count == 2
        assert (tmp_path / "t-aa").read_text(encoding="utf-8") == "a\nb\n"
        assert (tmp_path / "t-ab").read_text(encoding="utf-8") == "c\n"


class TestSplitFileBySize:
    def test_basic_size_split(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        lines = [f"line{i}" for i in range(100)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "size-"),
            max_bytes_per_chunk=200,
        )
        count = split_file(config)
        assert count > 1
        chunks = sorted(tmp_path.glob("size-*"))
        combined = ""
        for c in chunks:
            combined += c.read_text(encoding="utf-8")
        assert combined == "\n".join(lines)

    def test_no_line_split(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        long_line = "x" * 200
        lines = [long_line, "short", "a" * 300, "last"]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "no-split-"),
            max_bytes_per_chunk=300,
        )
        split_file(config)
        chunks = sorted(tmp_path.glob("no-split-*"))
        for chunk_path in chunks:
            content = chunk_path.read_text(encoding="utf-8")
            for chunk_line in content.splitlines():
                assert chunk_line in lines

    def test_single_line_larger_than_size(self, tmp_path: Path):
        input_file = tmp_path / "big_line.txt"
        huge_line = "x" * 5000
        input_file.write_text(huge_line, encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "big-"),
            max_bytes_per_chunk=100,
        )
        count = split_file(config)
        assert count == 1
        chunk = tmp_path / "big-aa"
        assert chunk.exists()
        assert chunk.read_text(encoding="utf-8") == huge_line

    def test_empty_file(self, tmp_path: Path):
        input_file = tmp_path / "empty.txt"
        input_file.write_text("", encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "e-"),
            max_bytes_per_chunk=100,
        )
        count = split_file(config)
        assert count == 0

    def test_exact_size_boundary(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        exact_line = "abc"
        input_file.write_text(exact_line, encoding="utf-8")

        config = SplitConfig(
            input_path=input_file,
            output_prefix=str(tmp_path / "exact-"),
            max_bytes_per_chunk=100,
        )
        count = split_file(config)
        assert count == 1
        assert (tmp_path / "exact-aa").read_text(encoding="utf-8") == "abc"


class TestCliSplit:
    def test_help(self):
        result = CliRunner().invoke(cli, ["file", "split", "--help"])
        assert result.exit_code == 0

    def test_no_mode_specified_fails(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        input_file.write_text("hello", encoding="utf-8")
        result = CliRunner().invoke(
            cli, ["file", "split", str(input_file), "--output-prefix", str(tmp_path / "x")]
        )
        assert result.exit_code != 0
        assert "必须指定" in result.output

    def test_both_modes_specified_fails(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        input_file.write_text("hello", encoding="utf-8")
        result = CliRunner().invoke(
            cli, [
                "file", "split", str(input_file),
                "--lines", "10",
                "--size", "1K",
                "--output-prefix", str(tmp_path / "x"),
            ]
        )
        assert result.exit_code != 0
        assert "不能同时指定" in result.output

    def test_missing_output_prefix_fails(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        input_file.write_text("hello", encoding="utf-8")
        result = CliRunner().invoke(
            cli, ["file", "split", str(input_file), "--lines", "10"]
        )
        assert result.exit_code != 0

    def test_basic_lines_split(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        lines = [f"line{i}" for i in range(100)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        result = CliRunner().invoke(
            cli, [
                "file", "split", str(input_file),
                "--lines", "30",
                "--output-prefix", str(tmp_path / "chunk-"),
            ]
        )
        assert result.exit_code == 0
        assert "4" in result.output
        assert (tmp_path / "chunk-aa").exists()
        assert (tmp_path / "chunk-ad").exists()

    def test_basic_size_split(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        lines = [f"line{i}" for i in range(100)]
        input_file.write_text("\n".join(lines), encoding="utf-8")

        result = CliRunner().invoke(
            cli, [
                "file", "split", str(input_file),
                "--size", "200",
                "--output-prefix", str(tmp_path / "size-"),
            ]
        )
        assert result.exit_code == 0
        chunks = sorted(tmp_path.glob("size-*"))
        assert len(chunks) > 1

    def test_numeric_suffix(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        input_file.write_text("a\nb\nc\nd\ne", encoding="utf-8")

        result = CliRunner().invoke(
            cli, [
                "file", "split", str(input_file),
                "--lines", "2",
                "--output-prefix", str(tmp_path / "n-"),
                "--numeric-suffix",
            ]
        )
        assert result.exit_code == 0
        assert (tmp_path / "n-00").exists()
        assert (tmp_path / "n-01").exists()
        assert (tmp_path / "n-02").exists()

    def test_custom_suffix_length(self, tmp_path: Path):
        input_file = tmp_path / "input.txt"
        input_file.write_text("a\nb\nc\nd\ne", encoding="utf-8")

        result = CliRunner().invoke(
            cli, [
                "file", "split", str(input_file),
                "--lines", "2",
                "--output-prefix", str(tmp_path / "l-"),
                "--suffix-length", "3",
            ]
        )
        assert result.exit_code == 0
        assert (tmp_path / "l-aaa").exists()
        assert (tmp_path / "l-aab").exists()
        assert (tmp_path / "l-aac").exists()
