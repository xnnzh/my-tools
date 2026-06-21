import base64
import re
import urllib.parse


def encode_unicode_text(text: str) -> str:
    result = []
    for c in text:
        cp = ord(c)
        if cp < 128:
            result.append(c)
        elif cp > 0xFFFF:
            high = 0xD800 + ((cp - 0x10000) >> 10)
            low = 0xDC00 + ((cp - 0x10000) & 0x3FF)
            result.append(f"\\u{high:04x}\\u{low:04x}")
        else:
            result.append(f"\\u{cp:04x}")
    return "".join(result)


_UNI_PREFIX_RE = re.compile(r"\\[uU]")


def decode_unicode_text(text: str) -> str:
    pos = 0
    parts = []
    while pos < len(text):
        m = _UNI_PREFIX_RE.match(text, pos)
        if not m:
            parts.append(text[pos])
            pos += 1
            continue

        prefix = m.group(0)
        is_upper = prefix == "\\U"
        required = 8 if is_upper else 4
        start = m.end()
        end = start + required
        if end > len(text):
            raise ValueError(
                f"{'\\\\U' if is_upper else '\\\\u'}后不足 {required} 位"
            )
        hex_part = text[start:end]
        if not re.match(r"^[0-9a-fA-F]+$", hex_part):
            raise ValueError(
                f"{'\\\\U' if is_upper else '\\\\u'}{hex_part} 不是合法十六进制"
            )

        cp = int(hex_part, 16)
        if cp > 0x10FFFF:
            raise ValueError(f"码点超出 Unicode 范围: U+{hex_part.upper()}")
        if 0xD800 <= cp <= 0xDBFF:
            next_prefix = _UNI_PREFIX_RE.match(text, end)
            if next_prefix and next_prefix.group(0) == "\\u":
                next_start = next_prefix.end()
                next_end = next_start + 4
                if next_end <= len(text):
                    next_hex = text[next_start:next_end]
                    if re.match(r"^[0-9a-fA-F]+$", next_hex):
                        next_cp = int(next_hex, 16)
                        if 0xDC00 <= next_cp <= 0xDFFF:
                            full = 0x10000 + ((cp - 0xD800) << 10) + (next_cp - 0xDC00)
                            parts.append(chr(full))
                            pos = next_end
                            continue
            raise ValueError(f"孤立代理项: U+{hex_part.upper()}")
        if 0xDC00 <= cp <= 0xDFFF:
            raise ValueError(f"孤立代理项: U+{hex_part.upper()}")
        parts.append(chr(cp))
        pos = end
    return "".join(parts)


def encode_utf8_text(text: str, *, encoding: str = "utf-8") -> str:
    return " ".join(f"{b:02x}" for b in text.encode(encoding))


_HEX_STRIP_RE = re.compile(r"[\s\\xX0-9xX]+")


def decode_utf8_text(text: str, *, encoding: str = "utf-8") -> str:
    stripped = re.sub(r"0x", "", text, flags=re.IGNORECASE)
    stripped = re.sub(r"\\x", "", stripped, flags=re.IGNORECASE)
    stripped = stripped.strip()
    if not stripped:
        raise ValueError("输入为空")
    hex_chars = re.sub(r"\s+", "", stripped)
    if len(hex_chars) == 0:
        raise ValueError("输入为空")
    if len(hex_chars) % 2 != 0:
        raise ValueError(f"hex 字符串长度为奇数: {len(hex_chars)}")
    if not re.match(r"^[0-9a-fA-F]+$", hex_chars):
        raise ValueError("包含非 hex 字符")
    data = bytes.fromhex(hex_chars)
    try:
        return data.decode(encoding)
    except UnicodeDecodeError as e:
        raise ValueError(str(e))


def encode_url_text(
    text: str,
    *,
    encoding: str = "utf-8",
    safe: str = "",
    plus: bool = False,
) -> str:
    if plus:
        return urllib.parse.quote_plus(text, safe=safe, encoding=encoding)
    return urllib.parse.quote(text, safe=safe, encoding=encoding)


def decode_url_text(
    text: str,
    *,
    encoding: str = "utf-8",
    plus: bool = False,
) -> str:
    if plus:
        return urllib.parse.unquote_plus(text, encoding=encoding)
    try:
        return urllib.parse.unquote(text, encoding=encoding, errors="strict")
    except UnicodeDecodeError as e:
        raise ValueError(str(e))


def _check_invalid_percent(text: str) -> None:
    i = 0
    while i < len(text):
        if text[i] == "%":
            if i + 2 >= len(text):
                raise ValueError(f"不完整的百分号编码: {text[i:]!r}")
            if not re.match(r"^[0-9a-fA-F]{2}", text[i + 1 : i + 3]):
                raise ValueError(
                    f"百分号后不是合法十六进制: {text[i:i+3]!r}"
                )
            i += 3
        else:
            i += 1


def encode_base_text(
    text: str,
    *,
    encoding: str = "utf-8",
    base: str = "64",
) -> str:
    data = text.encode(encoding)
    if base == "16":
        return base64.b16encode(data).decode("ascii")
    elif base == "32":
        return base64.b32encode(data).decode("ascii")
    elif base == "64":
        return base64.b64encode(data).decode("ascii")
    elif base == "85":
        return base64.b85encode(data).decode("ascii")
    else:
        raise ValueError(f"不支持的 Base 类型: {base}")


def decode_base_text(
    text: str,
    *,
    encoding: str = "utf-8",
    base: str = "64",
) -> str:
    cleaned = re.sub(r"\s+", "", text.strip())
    if not cleaned:
        raise ValueError("输入为空")
    try:
        if base == "16":
            data = base64.b16decode(cleaned)
        elif base == "32":
            data = base64.b32decode(cleaned)
        elif base == "64":
            data = base64.b64decode(cleaned, validate=True)
        elif base == "85":
            data = base64.b85decode(cleaned)
        else:
            raise ValueError(f"不支持的 Base 类型: {base}")
    except Exception as e:
        raise ValueError(str(e))
    try:
        return data.decode(encoding)
    except UnicodeDecodeError as e:
        raise ValueError(str(e))
