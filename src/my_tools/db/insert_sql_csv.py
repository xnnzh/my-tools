import csv
import re
from dataclasses import dataclass, field
from typing import TextIO


@dataclass
class InsertCsvData:
    columns: list[str]
    rows: list[list[str | None]]
    warnings: list[str] = field(default_factory=list)


_INSERT_RE = re.compile(r"^\s*insert\s+into\s+", re.IGNORECASE)


def parse_columns(columns_sql: str) -> list[str]:
    columns_sql = columns_sql.strip()
    if columns_sql.startswith("("):
        columns_sql = columns_sql[1:]
    if columns_sql.endswith(")"):
        columns_sql = columns_sql[:-1]

    cols: list[str] = []
    current: list[str] = []
    in_backtick = False

    for c in columns_sql:
        if in_backtick:
            if c == "`":
                in_backtick = False
            else:
                current.append(c)
        elif c == "`":
            in_backtick = True
        elif c == ",":
            col = "".join(current).strip()
            if col:
                cols.append(col)
            current = []
        else:
            current.append(c)

    last = "".join(current).strip()
    if last:
        cols.append(last)

    return cols


def parse_sql_literal(token: str) -> str | None:
    token = token.strip()
    if not token:
        return None
    if token.lower() == "null":
        return None
    if token.startswith("'") and token.endswith("'"):
        inner = token[1:-1]
        return inner.replace("''", "'")
    return token


def write_csv(data: InsertCsvData, output: TextIO, *, delimiter: str = ",") -> None:
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    writer.writerow(data.columns)
    writer.writerows(
        [v if v is not None else "" for v in row] for row in data.rows
    )


def _skip_to_column_list_paren(sql: str, start: int) -> int:
    i = start
    while i < len(sql):
        if sql[i] == "`":
            i += 1
            while i < len(sql) and sql[i] != "`":
                i += 1
        elif sql[i] == "(":
            return i
        elif (
            i + 6 <= len(sql)
            and sql[i : i + 6].lower() == "values"
            and (i == 0 or not sql[i - 1].isalnum())
            and (i + 6 >= len(sql) or not sql[i + 6].isalnum())
        ):
            return -1
        i += 1
    return -1


def _match_bracket(sql: str, start: int) -> int:
    depth = 0
    in_string = False
    in_backtick = False
    i = start
    while i < len(sql):
        c = sql[i]
        if in_string:
            if c == "'" and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 1
            elif c == "'":
                in_string = False
        elif in_backtick:
            if c == "`":
                in_backtick = False
        elif c == "'":
            in_string = True
        elif c == "`":
            in_backtick = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("括号不匹配")


def _find_values_keyword(sql: str, start: int) -> int:
    i = start
    in_string = False
    in_backtick = False
    while i < len(sql):
        c = sql[i]
        if in_string:
            if c == "'":
                if i + 1 < len(sql) and sql[i + 1] == "'":
                    i += 1
                else:
                    in_string = False
        elif in_backtick:
            if c == "`":
                in_backtick = False
        elif c == "'":
            in_string = True
        elif c == "`":
            in_backtick = True
        elif c == "-" and i + 1 < len(sql) and sql[i + 1] == "-":
            while i < len(sql) and sql[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < len(sql) and sql[i + 1] == "*":
            i += 2
            while i < len(sql):
                if sql[i] == "*" and i + 1 < len(sql) and sql[i + 1] == "/":
                    i += 1
                    break
                i += 1
        elif (
            i + 6 <= len(sql)
            and sql[i : i + 6].lower() == "values"
            and (i == 0 or not sql[i - 1].isalnum())
            and (i + 6 >= len(sql) or not sql[i + 6].isalnum())
        ):
            return i
        i += 1
    return -1


def _split_row_values(content: str) -> list[str]:
    values: list[str] = []
    current: list[str] = []
    depth = 0
    in_string = False
    i = 0
    while i < len(content):
        c = content[i]
        if in_string:
            current.append(c)
            if c == "'":
                if i + 1 < len(content) and content[i + 1] == "'":
                    current.append(content[i + 1])
                    i += 1
                else:
                    in_string = False
        else:
            if c == "'":
                in_string = True
                current.append(c)
            elif c == "(":
                depth += 1
                current.append(c)
            elif c == ")":
                depth -= 1
                current.append(c)
            elif c == "," and depth == 0:
                values.append("".join(current).strip())
                current = []
            else:
                current.append(c)
        i += 1
    last = "".join(current).strip()
    if last:
        values.append(last)
    return values


def parse_insert_sql(sql: str, *, strict: bool = False) -> InsertCsvData:
    warnings: list[str] = []
    sql = sql.strip()
    while sql.endswith(";"):
        sql = sql[:-1].strip()

    if not sql.lower().startswith("insert into"):
        raise ValueError("不支持的 INSERT 语句: 必须以 INSERT INTO 开头")

    m = _INSERT_RE.match(sql)
    if not m:
        raise ValueError("不支持的 INSERT 语句: 必须以 INSERT INTO 开头")

    pos = m.end()

    col_start = _skip_to_column_list_paren(sql, pos)
    if col_start < 0 or col_start >= len(sql) or sql[col_start] != "(":
        raise ValueError("不支持: INSERT SQL 缺少列名列表，无法生成 CSV 标题")

    col_end = _match_bracket(sql, col_start)
    columns = parse_columns(sql[col_start : col_end + 1])
    if not columns:
        raise ValueError("列名列表为空")

    pos = col_end + 1

    check_select = sql[col_end + 1:].lstrip().lower()
    if check_select.startswith("select"):
        raise ValueError("暂不支持 INSERT ... SELECT")

    values_pos = _find_values_keyword(sql, pos)
    if values_pos < 0:
        raise ValueError("不支持: 未找到 VALUES 关键字")

    pos = values_pos + 6

    rows: list[list[str]] = []

    while pos < len(sql):
        while pos < len(sql) and sql[pos] in " \t\n\r,":
            pos += 1
        if pos >= len(sql):
            break
        if sql[pos] != "(":
            break

        row_end = _match_bracket(sql, pos)
        row_content = sql[pos + 1 : row_end]
        row_values = _split_row_values(row_content)
        rows.append(row_values)
        pos = row_end + 1

    if not rows:
        raise ValueError("未找到任何 VALUES 行")

    num_cols = len(columns)
    normalized_rows: list[list[str | None]] = []

    for row_idx, row in enumerate(rows):
        if len(row) < num_cols:
            msg = (
                f"第 {row_idx + 1} 行值数量 ({len(row)}) 少于列数 ({num_cols})"
                f"，缺少字段补空"
            )
            warnings.append(msg)
            if strict:
                raise ValueError(msg)
            row = row + [None] * (num_cols - len(row))
        elif len(row) > num_cols:
            msg = (
                f"第 {row_idx + 1} 行值数量 ({len(row)}) 多于列数 ({num_cols})"
                f"，丢弃多余字段"
            )
            warnings.append(msg)
            if strict:
                raise ValueError(msg)
            row = row[:num_cols]

        normalized_rows.append([parse_sql_literal(v) if v is not None else None for v in row])

    return InsertCsvData(
        columns=columns, rows=normalized_rows, warnings=warnings
    )
