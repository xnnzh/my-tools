import json


def _strip_bom(text: str) -> str:
    return text.lstrip("\ufeff")


def _load_json(text: str):
    text = _strip_bom(text).strip()
    if not text:
        raise ValueError("JSON 内容为空")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {e.msg}")


def pretty_json(
    text: str,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
) -> str:
    if indent < 0:
        raise ValueError("缩进空格数不能小于 0")
    obj = _load_json(text)
    return json.dumps(
        obj, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys
    )


def compact_json(
    text: str,
    *,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
) -> str:
    obj = _load_json(text)
    return json.dumps(
        obj,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
        separators=(",", ":"),
    )


def escape_json_text(
    text: str,
    *,
    wrap: bool = False,
    ensure_ascii: bool = False,
) -> str:
    escaped = json.dumps(text, ensure_ascii=ensure_ascii)
    if wrap:
        return escaped
    return escaped[1:-1]


def unescape_json_text(text: str) -> str:
    candidate = text.strip()
    if not candidate:
        return ""

    try:
        if candidate.startswith('"') and candidate.endswith('"'):
            value = json.loads(candidate)
        else:
            value = json.loads(f'"{candidate}"')
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 转义内容解析失败: {e.msg}")

    if not isinstance(value, str):
        raise ValueError("输入不是 JSON 字符串")
    return value
