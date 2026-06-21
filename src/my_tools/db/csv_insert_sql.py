import csv
import io
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExtraField:
    name: str
    value: str
    raw_sql: bool = False


@dataclass(frozen=True)
class CsvInsertResult:
    sql: str
    warnings: list[str] = field(default_factory=list)


def parse_field_list(text: str | None) -> list[str] | None:
    if text is None:
        return None
    return [f.strip() for f in text.split(",") if f.strip()]


def parse_extra_assignment(text: str, *, raw_sql: bool = False) -> ExtraField:
    if "=" not in text:
        raise ValueError(f"缺少 '=': {text!r}")
    name, _, value = text.partition("=")
    if not name.strip():
        raise ValueError(f"字段名不能为空: {text!r}")
    return ExtraField(name=name.strip(), value=value, raw_sql=raw_sql)


def parse_field_types(text: str | None) -> dict[str, str]:
    if text is None:
        return {}
    result = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"字段类型格式错误，缺少 ':': {part!r}")
        name, _, ft = part.partition(":")
        name = name.strip()
        ft = ft.strip()
        if not name:
            raise ValueError(f"字段名不能为空: {part!r}")
        if ft not in ("string", "number", "boolean", "sql", "null"):
            raise ValueError(f"不支持的字段类型: {ft!r}")
        if name in result and result[name] != ft:
            raise ValueError(
                f"字段 {name!r} 类型冲突: {result[name]!r} vs {ft!r}"
            )
        result[name] = ft
    return result


def merge_field_types(
    *,
    field_types: dict[str, str] | None = None,
    number_fields: list[str] | None = None,
    boolean_fields: list[str] | None = None,
    extra_fields: list[ExtraField] | None = None,
) -> dict[str, str]:
    result = dict(field_types or {})

    if number_fields:
        for name in number_fields:
            if name in result and result[name] != "number":
                raise ValueError(
                    f"字段 {name!r} 类型冲突: {result[name]!r} vs 'number'"
                )
            result[name] = "number"

    if boolean_fields:
        for name in boolean_fields:
            if name in result and result[name] != "boolean":
                raise ValueError(
                    f"字段 {name!r} 类型冲突: {result[name]!r} vs 'boolean'"
                )
            result[name] = "boolean"

    if extra_fields:
        for ef in extra_fields:
            if ef.raw_sql:
                inferred = "sql"
            else:
                inferred = "string"
            if ef.name not in result:
                result[ef.name] = inferred

    return result


def quote_identifier(name: str) -> str:
    if not name:
        raise ValueError("标识符不能为空")
    return f"`{name.replace('`', '``')}`"


def quote_table(database: str | None, table: str) -> str:
    if not table:
        raise ValueError("表名不能为空")
    if "." in table:
        raise ValueError(
            f"表名中不能包含 '.': {table!r}，请使用 --database db --table table"
        )
    q = quote_identifier(table)
    if database:
        q = f"{quote_identifier(database)}.{q}"
    return q


def _escape_sql_string(value: str) -> str:
    if "\x00" in value:
        raise ValueError("字符串包含 NUL 字符")
    value = value.replace("\\", "\\\\")
    value = value.replace("'", "''")
    return value


def _parse_bool(value: str) -> bool:
    if value.lower() in ("true", "1", "yes", "y"):
        return True
    if value.lower() in ("false", "0", "no", "n"):
        return False
    raise ValueError(f"无法识别为布尔值: {value!r}")


def sql_literal(value: str | None, *, field_type: str = "string") -> str:
    if value is None or value == "":
        return "NULL"
    if field_type == "string":
        return f"'{_escape_sql_string(value)}'"
    elif field_type == "number":
        if not re.match(r"^-?\d+(\.\d+)?$", value.strip()):
            raise ValueError(f"非法数字: {value!r}")
        return value.strip()
    elif field_type == "boolean":
        return "TRUE" if _parse_bool(value) else "FALSE"
    elif field_type == "sql":
        return value
    elif field_type == "null":
        return "NULL"
    else:
        raise ValueError(f"不支持的字段类型: {field_type!r}")


def convert_csv_to_insert_sql(
    text: str,
    *,
    table: str,
    database: str | None = None,
    fields: list[str] | None = None,
    exclude_fields: list[str] | None = None,
    extra_fields: list[ExtraField] | None = None,
    field_types: dict[str, str] | None = None,
    delimiter: str = ",",
    batch: bool = True,
    batch_size: int = 1000,
    strict: bool = False,
) -> CsvInsertResult:
    warnings: list[str] = []
    all_extra = extra_fields or []
    types = field_types or {}

    if fields is not None and exclude_fields is not None:
        raise ValueError("--fields 与 --exclude-fields 不能同时指定")

    if batch_size < 1:
        raise ValueError(f"batch-size 必须为正整数: {batch_size}")

    raw = text.lstrip("\ufeff").strip()
    if not raw:
        raise ValueError("CSV 内容为空")

    reader = csv.DictReader(io.StringIO(raw), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("CSV 缺少表头")

    headers = reader.fieldnames

    if fields is not None:
        for f in fields:
            if f not in headers:
                raise ValueError(f"字段 {f!r} 不存在于 CSV 中")
        selected = fields
    elif exclude_fields is not None:
        selected = [h for h in headers if h not in set(exclude_fields)]
        for ef in exclude_fields:
            if ef not in headers:
                msg = f"要排除的字段 {ef!r} 不存在于 CSV 中"
                if strict:
                    raise ValueError(msg)
                warnings.append(msg)
    else:
        selected = list(headers)

    extra_names = [ef.name for ef in all_extra]
    if extra_names:
        for ef in all_extra:
            if ef.name in selected:
                raise ValueError(
                    f"额外字段 {ef.name!r} 与 CSV 字段重名"
                )
        if len(extra_names) != len(set(extra_names)):
            raise ValueError("额外字段之间存在重名")

    all_columns = selected + extra_names
    merged_types = merge_field_types(
        field_types=types,
        extra_fields=all_extra,
    )

    for name in merged_types:
        if name not in all_columns:
            raise ValueError(
                f"类型声明的字段 {name!r} 不存在于最终输出列中"
            )

    rows = list(reader)
    if not rows:
        return CsvInsertResult(sql="", warnings=warnings)

    q_table = quote_table(database, table)
    q_columns = ", ".join(quote_identifier(c) for c in all_columns)

    def _make_values(row: dict[str, str]) -> str:
        vals = []
        for col in all_columns:
            if col in extra_names:
                ef = next(e for e in all_extra if e.name == col)
                ft = merged_types.get(col, "sql" if ef.raw_sql else "string")
                vals.append(sql_literal(ef.value, field_type=ft))
            else:
                raw_val = row.get(col)
                ft = merged_types.get(col, "string")
                vals.append(sql_literal(raw_val, field_type=ft))
        return f"({', '.join(vals)})"

    if not batch:
        batch_size = 1

    parts: list[str] = []
    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        values_lines = ",\n".join(
            f"  {_make_values(r)}" for r in chunk
        )
        parts.append(
            f"INSERT INTO {q_table} ({q_columns})\nVALUES\n{values_lines};"
        )

    sql = "\n\n".join(parts) + "\n"
    return CsvInsertResult(sql=sql, warnings=warnings)
