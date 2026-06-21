import sys

import click

from .converter import (
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_TIMEZONE,
    datetime_to_timestamp,
    timestamp_to_datetime,
)


def _collect_values(value: str | None) -> list[str]:
    if value is not None:
        return [value]
    lines = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]
    if not lines:
        raise click.ClickException("请通过参数或 stdin 提供输入")
    return lines


@click.group(name="time")
def time_group():
    """日期时间工具。"""


@time_group.command("to-timestamp")
@click.argument("datetime_text", required=False)
@click.option(
    "-z",
    "--timezone",
    default=DEFAULT_TIMEZONE,
    show_default=True,
    help="时区",
)
@click.option(
    "-u",
    "--unit",
    type=click.Choice(["s", "ms"]),
    default="ms",
    show_default=True,
    help="输出时间戳单位：s 秒，ms 毫秒",
)
@click.option(
    "--input-format",
    help="输入日期时间格式，例如 %%Y-%%m-%%d %%H:%%M:%%S",
)
@click.option("--strict", is_flag=True, help="解析失败时返回错误")
def to_timestamp(datetime_text, timezone, unit, input_format, strict):
    """将日期时间转换为时间戳。"""
    values = _collect_values(datetime_text)
    results = []
    for val in values:
        try:
            ts = datetime_to_timestamp(
                val, timezone=timezone, unit=unit, input_format=input_format
            )
            results.append(str(ts))
        except ValueError as e:
            if strict:
                raise click.ClickException(str(e))
            click.echo(f"Warning: {e}", err=True)
    click.echo("\n".join(results))


@time_group.command("from-timestamp")
@click.argument("timestamp", required=False)
@click.option(
    "-z",
    "--timezone",
    default=DEFAULT_TIMEZONE,
    show_default=True,
    help="输出时区",
)
@click.option(
    "-u",
    "--unit",
    type=click.Choice(["s", "ms"]),
    default="ms",
    show_default=True,
    help="输入时间戳单位：s 秒，ms 毫秒",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    default=DEFAULT_OUTPUT_FORMAT,
    show_default=True,
    help="输出日期时间格式",
)
@click.option("--strict", is_flag=True, help="解析失败时返回错误")
def from_timestamp(timestamp, timezone, unit, output_format, strict):
    """将时间戳转换为日期时间。"""
    values = _collect_values(timestamp)
    results = []
    for val in values:
        try:
            dt = timestamp_to_datetime(
                val,
                timezone=timezone,
                unit=unit,
                output_format=output_format,
            )
            results.append(dt)
        except (ValueError, OSError) as e:
            if strict:
                raise click.ClickException(str(e))
            click.echo(f"Warning: {e}", err=True)
    click.echo("\n".join(results))
