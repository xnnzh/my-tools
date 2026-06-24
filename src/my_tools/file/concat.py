import os
from pathlib import Path


def collect_files(
    path: str,
    *,
    skip_hidden: bool = True,
    extensions: tuple[str, ...] | None = None,
) -> list[Path]:
    p = Path(path)
    if p.is_file():
        return [p]

    files: list[Path] = []
    for child in p.iterdir():
        if not child.is_file():
            continue
        if skip_hidden and child.name.startswith("."):
            continue
        if extensions and child.suffix not in extensions:
            continue
        files.append(child)

    return sort_files(files)


def sort_files(files: list[Path]) -> list[Path]:
    return sorted(files, key=lambda p: (len(p.name), p.name))


def read_file_content(
    path: Path,
    *,
    encoding: str,
    skip_empty: bool,
) -> str | None:
    content = path.read_text(encoding=encoding)
    if skip_empty and not content.strip():
        return None
    return content


def concatenate_files(
    paths: list[str],
    *,
    encoding: str = "utf-8",
    skip_empty: bool = False,
    skip_hidden: bool = True,
    extensions: tuple[str, ...] | None = None,
    separator: str = "",
) -> str:
    parts: list[str] = []

    for input_path in paths:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"路径不存在: {input_path}")

        files = collect_files(
            input_path,
            skip_hidden=skip_hidden,
            extensions=extensions,
        )

        for f in files:
            content = read_file_content(f, encoding=encoding, skip_empty=skip_empty)
            if content is not None:
                if parts and separator:
                    parts.append(separator)
                parts.append(content)

    return "".join(parts)
