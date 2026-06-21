import pytest
from click.testing import CliRunner

from my_tools.cli import cli
from my_tools.time_tools.converter import (
    datetime_to_timestamp,
    get_timezone,
    parse_datetime,
    timestamp_to_datetime,
)


class TestGetTimezone:
    def test_default(self):
        tz = get_timezone("Asia/Shanghai")
        assert str(tz) == "Asia/Shanghai"

    def test_utc(self):
        tz = get_timezone("UTC")
        assert str(tz) == "UTC"

    def test_offset_positive(self):
        tz = get_timezone("+08:00")
        assert str(tz) == "UTC+08:00"

    def test_offset_negative(self):
        tz = get_timezone("-05:00")
        assert str(tz) == "UTC-05:00"

    def test_offset_no_colon(self):
        tz = get_timezone("+0800")
        assert str(tz) == "UTC+08:00"

    def test_invalid_zone(self):
        with pytest.raises(ValueError, match="不支持的时区"):
            get_timezone("Bad/Zone")


class TestParseDatetime:
    def test_simple(self):
        dt = parse_datetime("1970-01-01 08:00:00")
        assert dt.tzinfo is not None

    def test_with_iso_tz(self):
        dt = parse_datetime("1970-01-01T08:00:00+08:00")
        assert dt.tzinfo is not None

    def test_with_z(self):
        dt = parse_datetime("1970-01-01T00:00:00Z")
        assert dt.tzinfo is not None

    def test_date_only(self):
        dt = parse_datetime("1970-01-01")
        assert dt.tzinfo is not None

    def test_custom_format(self):
        dt = parse_datetime("1970/01/01 08:00:00", input_format="%Y/%m/%d %H:%M:%S")
        assert dt.year == 1970

    def test_invalid(self):
        with pytest.raises(ValueError):
            parse_datetime("not-a-date")


class TestDatetimeToTimestamp:
    def test_epoch_ms_default(self):
        assert datetime_to_timestamp("1970-01-01 08:00:00") == 0

    def test_epoch_s(self):
        assert datetime_to_timestamp("1970-01-01 08:00:01", unit="s") == 1

    def test_utc_timezone(self):
        assert datetime_to_timestamp("1970-01-01 00:00:00", timezone="UTC") == 0

    def test_iso_with_tz(self):
        assert datetime_to_timestamp("1970-01-01T08:00:00+08:00") == 0

    def test_date_only(self):
        assert datetime_to_timestamp("1970-01-01") == -28800000

    def test_custom_format(self):
        assert (
            datetime_to_timestamp(
                "1970/01/01 08:00:00", input_format="%Y/%m/%d %H:%M:%S"
            )
            == 0
        )

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="不支持的时间戳单位"):
            datetime_to_timestamp("1970-01-01 08:00:00", unit="minute")

    def test_offset_timezone(self):
        assert datetime_to_timestamp("1970-01-01 08:00:00", timezone="+08:00") == 0


class TestTimestampToDatetime:
    def test_epoch_ms_default(self):
        assert timestamp_to_datetime(0) == "1970-01-01 08:00:00"

    def test_epoch_s(self):
        assert timestamp_to_datetime(1, unit="s") == "1970-01-01 08:00:01"

    def test_utc_timezone(self):
        assert timestamp_to_datetime(0, timezone="UTC") == "1970-01-01 00:00:00"

    def test_offset_timezone(self):
        assert timestamp_to_datetime(0, timezone="+08:00") == "1970-01-01 08:00:00"

    def test_custom_format(self):
        assert (
            timestamp_to_datetime(0, output_format="%Y-%m-%dT%H:%M:%S%z")
            == "1970-01-01T08:00:00+0800"
        )

    def test_string_input(self):
        assert timestamp_to_datetime("0") == "1970-01-01 08:00:00"

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="不支持的时间戳单位"):
            timestamp_to_datetime(0, unit="minute")

    def test_invalid_timezone(self):
        with pytest.raises(ValueError, match="不支持的时区"):
            timestamp_to_datetime(0, timezone="Bad/Zone")

    def test_negative_timestamp(self):
        assert timestamp_to_datetime(-28800000) == "1970-01-01 00:00:00"


class TestCli:
    def test_group_help(self):
        result = CliRunner().invoke(cli, ["time", "--help"])
        assert result.exit_code == 0
        assert "to-timestamp" in result.output
        assert "from-timestamp" in result.output

    def test_to_timestamp_help(self):
        result = CliRunner().invoke(cli, ["time", "to-timestamp", "--help"])
        assert result.exit_code == 0
        assert "--timezone" in result.output
        assert "--unit" in result.output
        assert "--input-format" in result.output

    def test_from_timestamp_help(self):
        result = CliRunner().invoke(cli, ["time", "from-timestamp", "--help"])
        assert result.exit_code == 0
        assert "--timezone" in result.output
        assert "--unit" in result.output
        assert "--format" in result.output

    def test_to_timestamp_arg(self):
        result = CliRunner().invoke(cli, ["time", "to-timestamp", "1970-01-01 08:00:00"])
        assert result.exit_code == 0
        assert result.output.strip() == "0"

    def test_from_timestamp_arg(self):
        result = CliRunner().invoke(cli, ["time", "from-timestamp", "0"])
        assert result.exit_code == 0
        assert result.output.strip() == "1970-01-01 08:00:00"

    def test_to_timestamp_unit_s(self):
        result = CliRunner().invoke(
            cli, ["time", "to-timestamp", "1970-01-01 08:00:01", "--unit", "s"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "1"

    def test_from_timestamp_unit_s(self):
        result = CliRunner().invoke(
            cli, ["time", "from-timestamp", "1", "--unit", "s"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "1970-01-01 08:00:01"

    def test_to_timestamp_stdin(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["time", "to-timestamp"],
            input="1970-01-01 08:00:00\n1970-01-01 08:00:01\n",
        )
        assert result.exit_code == 0
        lines = result.output.strip().splitlines()
        assert lines == ["0", "1000"]

    def test_from_timestamp_stdin(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["time", "from-timestamp"],
            input="0\n1000\n",
        )
        assert result.exit_code == 0
        lines = result.output.strip().splitlines()
        assert lines == ["1970-01-01 08:00:00", "1970-01-01 08:00:01"]

    def test_strict_failure(self):
        result = CliRunner().invoke(
            cli, ["time", "to-timestamp", "bad-date", "--strict"]
        )
        assert result.exit_code != 0

    def test_non_strict_skip(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["time", "to-timestamp"],
            input="1970-01-01 08:00:00\nbad-date\n1970-01-01 08:00:01\n",
        )
        assert result.exit_code == 0
        lines = [line for line in result.output.strip().splitlines() if not line.startswith("Warning")]
        assert lines == ["0", "1000"]

    def test_no_input(self):
        result = CliRunner().invoke(cli, ["time", "to-timestamp"])
        assert result.exit_code != 0
        assert "请通过参数或 stdin 提供输入" in result.output

    def test_utc_timezone(self):
        result = CliRunner().invoke(
            cli, ["time", "to-timestamp", "1970-01-01 00:00:00", "--timezone", "UTC"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "0"

    def test_from_timestamp_utc(self):
        result = CliRunner().invoke(
            cli, ["time", "from-timestamp", "0", "--timezone", "UTC"]
        )
        assert result.exit_code == 0
        assert result.output.strip() == "1970-01-01 00:00:00"
