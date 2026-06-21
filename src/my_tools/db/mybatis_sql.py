from dataclasses import dataclass

_NUMERIC_TYPES = frozenset({
    "Byte", "Short", "Integer", "Long", "Float", "Double",
    "BigDecimal", "BigInteger",
})
_DATE_TYPES = frozenset({
    "Date", "Time", "Timestamp",
    "LocalDate", "LocalDateTime", "LocalTime",
    "OffsetDateTime", "ZonedDateTime",
})


@dataclass(frozen=True)
class SqlValue:
    raw: str | None
    type_name: str | None = None


def to_sql_literal(value: SqlValue) -> str:
    if value.raw is None:
        return "NULL"
    if value.type_name in _NUMERIC_TYPES:
        return value.raw
    if value.type_name == "Boolean":
        return "TRUE" if value.raw.lower() == "true" else "FALSE"
    escaped = value.raw.replace("'", "''")
    return f"'{escaped}'"


def parse_parameter_list(parameters: str) -> list[SqlValue]:
    result = []
    i = 0
    n = len(parameters)

    while i < n:
        while i < n and parameters[i] in " ,":
            i += 1
        if i >= n:
            break

        rest = parameters[i:]

        if rest.startswith("null") and (
            len(rest) == 4 or rest[4] in " ,)("
        ):
            if len(rest) > 4 and rest[4] == "(":
                j = rest.index(")", 5)
                type_name = rest[5:j].strip()
                result.append(SqlValue(raw=None, type_name=type_name or None))
                i += j + 1
            else:
                result.append(SqlValue(raw=None))
                i += 4
            continue

        j = i
        while j < n:
            if parameters[j] == ")":
                k = j + 1
                while k < n and parameters[k] == " ":
                    k += 1
                if k >= n or parameters[k] == ",":
                    idx = parameters.rfind("(", i, j)
                    if idx != -1:
                        value = parameters[i:idx].strip()
                        type_name = parameters[idx + 1 : j].strip()
                        result.append(
                            SqlValue(raw=value, type_name=type_name or None)
                        )
                        i = k
                        break
                j += 1
            else:
                j += 1
        else:
            result.append(SqlValue(raw=parameters[i:].strip()))
            break

    return result


def inline_parameters(
    sql: str, params: list[SqlValue], *, strict: bool = False
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    output: list[str] = []
    i = 0
    n = len(sql)
    param_idx = 0
    state = "normal"

    while i < n:
        c = sql[i]

        if state == "normal":
            if c == "'":
                state = "single_quote"
                output.append(c)
            elif c == '"':
                state = "double_quote"
                output.append(c)
            elif c == "`":
                state = "backtick"
                output.append(c)
            elif c == "-" and i + 1 < n and sql[i + 1] == "-":
                state = "line_comment"
                output.append(c)
            elif c == "/" and i + 1 < n and sql[i + 1] == "*":
                state = "block_comment"
                output.append(c)
                i += 1
                output.append(sql[i])
            elif c == "?":
                if param_idx < len(params):
                    output.append(to_sql_literal(params[param_idx]))
                    param_idx += 1
                else:
                    msg = (f"参数数量不足: 已替换 {param_idx} 个，"
                           f"仍有剩余占位符")
                    warnings.append(msg)
                    if strict:
                        return "", warnings
                    output.append("?")
            else:
                output.append(c)
        elif state == "single_quote":
            if c == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    output.append("''")
                    i += 1
                else:
                    state = "normal"
                    output.append(c)
            else:
                output.append(c)
        elif state == "double_quote":
            if c == '"':
                state = "normal"
            output.append(c)
        elif state == "backtick":
            if c == "`":
                state = "normal"
            output.append(c)
        elif state == "line_comment":
            if c == "\n":
                state = "normal"
            output.append(c)
        elif state == "block_comment":
            if c == "*" and i + 1 < n and sql[i + 1] == "/":
                output.append("*/")
                i += 1
                state = "normal"
            else:
                output.append(c)

        i += 1

    if param_idx < len(params):
        warnings.append(
            f"参数数量多于占位符: 提供了 {len(params)} 个参数，"
            f"只使用了 {param_idx} 个"
        )
        if strict:
            return "", warnings

    return "".join(output), warnings


def format_mybatis_log(
    text: str,
    *,
    mode: str = "replace",
    semicolon: bool = True,
    blank_line: bool = True,
    strict: bool = False,
) -> tuple[str, list[str]]:
    if mode not in ("replace", "append", "sql-only"):
        raise ValueError(f"未知的 mode: {mode}")

    lines = text.splitlines(keepends=True)
    all_warnings: list[str] = []

    blocks: list[tuple[int, int | None, str | None]] = []

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        pi = line.find("Preparing:")
        if pi == -1:
            i += 1
            continue

        sql = line[pi + len("Preparing:"):].strip()

        params_idx: int | None = None
        j = i + 1
        while j < len(lines):
            if "Parameters:" in lines[j]:
                params_idx = j
                break
            if "Preparing:" in lines[j]:
                break
            j += 1

        block_warnings: list[str] = []
        converted_sql: str | None = None

        if params_idx is not None:
            p_line = lines[params_idx].rstrip("\n")
            pk = p_line.find("Parameters:")
            params_str = p_line[pk + len("Parameters:"):].strip()
            params = parse_parameter_list(params_str)
            converted_sql, sub_warnings = inline_parameters(
                sql, params, strict=strict
            )
            block_warnings.extend(sub_warnings)
        else:
            if "?" in sql:
                block_warnings.append(
                    "SQL 包含占位符 ? 但未找到对应的 Parameters:"
                )
                if strict:
                    return "", block_warnings
            converted_sql = sql

        if converted_sql is not None and semicolon and not converted_sql.endswith(";"):
            converted_sql += ";"

        blocks.append((i, params_idx, converted_sql, block_warnings))

        if params_idx is not None:
            i = params_idx + 1
        else:
            i += 1

    for _, _, _, bw in blocks:
        all_warnings.extend(bw)

    if mode == "sql-only":
        sql_lines: list[str] = []
        first = True
        for _, _, csql, _ in blocks:
            if csql is None:
                continue
            if not first and blank_line:
                sql_lines.append("")
            sql_lines.append(csql)
            first = False
        return "\n".join(sql_lines), all_warnings

    consumed: set[int] = set()
    for pi, ppi, _, _ in blocks:
        start = pi
        end = ppi if ppi is not None else pi
        for k in range(start, end + 1):
            consumed.add(k)

    output_lines: list[str] = []
    i = 0
    while i < len(lines):
        if i in consumed:
            block = next(b for b in blocks if b[0] == i)
            pi, ppi, csql, _ = block
            if mode == "replace":
                output_lines.append(csql + "\n")
                i = (ppi if ppi is not None else pi) + 1
            else:
                output_lines.append(lines[i])
                if ppi is not None and ppi > pi:
                    for k in range(pi + 1, ppi):
                        output_lines.append(lines[k])
                    output_lines.append(lines[ppi])
                output_lines.append(f"-- Formatted SQL:\n{csql}\n")
                i = (ppi if ppi is not None else pi) + 1
        else:
            output_lines.append(lines[i])
            i += 1

    return "".join(output_lines), all_warnings
