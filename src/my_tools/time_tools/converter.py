import re
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_OUTPUT_FORMAT = "%Y-%m-%d %H:%M:%S"

_OFFSET_RE = re.compile(r"^([+-])(\d{2}):?(\d{2})$")
_ISO_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d",
]


def get_timezone(name: str) -> timezone | ZoneInfo:
    m = _OFFSET_RE.match(name)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        hours = int(m.group(2))
        minutes = int(m.group(3))
        offset = timedelta(hours=hours, minutes=minutes) * sign
        return timezone(offset)
    if name.upper() == "UTC":
        return UTC
    try:
        return ZoneInfo(name)
    except (KeyError, TypeError):
        raise ValueError(f"不支持的时区: {name}")


def parse_datetime(
    value: str,
    *,
    timezone: str = DEFAULT_TIMEZONE,
    input_format: str | None = None,
) -> datetime:
    if input_format:
        dt = datetime.strptime(value, input_format)
        return dt.replace(tzinfo=get_timezone(timezone))

    text = value.rstrip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    if "T" in text and ("+" in text[1:] or "-" in text.split("T")[1]):
        try:
            dt = datetime.fromisoformat(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=get_timezone(timezone))
            return dt
        except ValueError:
            pass

    for fmt in _ISO_FORMATS:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=get_timezone(timezone))
        except ValueError:
            continue

    raise ValueError(f"无法解析日期时间: {value}")


def datetime_to_timestamp(
    value: str,
    *,
    timezone: str = DEFAULT_TIMEZONE,
    unit: str = "ms",
    input_format: str | None = None,
) -> int:
    if unit not in ("s", "ms"):
        raise ValueError(f"不支持的时间戳单位: {unit}")
    dt = parse_datetime(value, timezone=timezone, input_format=input_format)
    epoch = dt.timestamp()
    if unit == "ms":
        return int(epoch * 1000)
    return int(epoch)


def timestamp_to_datetime(
    value: str | int | float,
    *,
    timezone: str = DEFAULT_TIMEZONE,
    unit: str = "ms",
    output_format: str = DEFAULT_OUTPUT_FORMAT,
) -> str:
    if unit not in ("s", "ms"):
        raise ValueError(f"不支持的时间戳单位: {unit}")
    ts = float(value)
    if unit == "ms":
        ts = ts / 1000
    tz = get_timezone(timezone)
    dt = datetime.fromtimestamp(ts, tz=tz)
    return dt.strftime(output_format)
