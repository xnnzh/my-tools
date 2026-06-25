def reverse_lines(
    content: str,
    *,
    keep_empty: bool = True,
) -> str:
    lines = content.splitlines(keepends=False)
    if not keep_empty:
        lines = [line for line in lines if line.strip()]
    lines.reverse()
    return "\n".join(lines)
