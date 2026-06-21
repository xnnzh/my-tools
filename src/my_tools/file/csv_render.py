import csv
import io
import re
from dataclasses import dataclass, field

DEFAULT_TEMPLATE = (
    "{@timestamp} {level} [{thread_name}] {logger_name} - {message}"
)

_FIELD_RE = re.compile(r"\{([^{}]+)\}")


@dataclass(frozen=True)
class RenderResult:
    lines: list[str]
    warnings: list[str] = field(default_factory=list)


def extract_template_fields(template: str) -> set[str]:
    return set(_FIELD_RE.findall(template))


def render_template(
    template: str,
    row: dict[str, str],
    *,
    strict: bool = False,
) -> tuple[str, list[str]]:
    warnings: list[str] = []

    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in row:
            msg = f"模板字段不存在: {key}"
            if strict:
                raise ValueError(msg)
            warnings.append(msg)
            return ""
        return row[key] or ""

    result = _FIELD_RE.sub(replace, template)
    return result, warnings


def convert_csv(
    text: str,
    *,
    template: str = DEFAULT_TEMPLATE,
    strict: bool = False,
) -> RenderResult:
    text = text.strip()
    text = text.lstrip("\ufeff")
    if not text:
        raise ValueError("CSV 内容为空")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV 缺少表头")

    headers = list(reader.fieldnames)

    all_warnings: list[str] = []

    template_fields = extract_template_fields(template)
    missing_fields = template_fields - set(headers)
    for missing_field in sorted(missing_fields):
        msg = f"模板字段 {missing_field} 在 CSV 中不存在"
        if strict:
            raise ValueError(msg)
        all_warnings.append(msg)

    lines: list[str] = []
    for row_num, row in enumerate(reader, 1):
        try:
            rendered, row_warnings = render_template(
                template, row, strict=strict
            )
        except ValueError as e:
            all_warnings.append(f"第 {row_num} 行渲染失败: {e}")
            if strict:
                raise
            continue
        for w in row_warnings:
            full_msg = f"第 {row_num} 行: {w}"
            if full_msg not in all_warnings:
                all_warnings.append(full_msg)
        lines.append(rendered)

    return RenderResult(lines=lines, warnings=all_warnings)
