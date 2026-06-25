def wrap_lines(
    text: str,
    prefix: str,
    *,
    suffix: str = "",
    last_suffix: str | None = None,
    keep_empty: bool = False,
) -> str:
    lines = text.splitlines(keepends=False)
    if not keep_empty:
        lines = [line for line in lines if line.strip() != ""]
    if not lines:
        return ""
    result = []
    for i, line in enumerate(lines):
        if i == len(lines) - 1:
            result.append(prefix + line + (last_suffix if last_suffix is not None else suffix))
        else:
            result.append(prefix + line + suffix)
    return "\n".join(result)
