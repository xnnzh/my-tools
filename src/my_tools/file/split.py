from dataclasses import dataclass
from pathlib import Path

_SIZE_UNITS: dict[str, int] = {
    "K": 1024,
    "KiB": 1024,
    "KB": 1000,
    "M": 1024 * 1024,
    "MiB": 1024 * 1024,
    "MB": 1000 * 1000,
    "G": 1024 ** 3,
    "GiB": 1024 ** 3,
    "GB": 1000 ** 3,
    "T": 1024 ** 4,
    "TiB": 1024 ** 4,
    "TB": 1000 ** 4,
    "P": 1024 ** 5,
    "PiB": 1024 ** 5,
    "PB": 1000 ** 5,
    "E": 1024 ** 6,
    "EiB": 1024 ** 6,
    "EB": 1000 ** 6,
    "Z": 1024 ** 7,
    "ZiB": 1024 ** 7,
    "ZB": 1000 ** 7,
    "Y": 1024 ** 8,
    "YiB": 1024 ** 8,
    "YB": 1000 ** 8,
}


@dataclass
class SplitConfig:
    input_path: Path
    output_prefix: str
    lines_per_chunk: int | None = None
    max_bytes_per_chunk: int | None = None
    suffix_length: int = 2
    numbering_start: int = 0
    numeric_suffix: bool = False
    encoding: str = "utf-8"


def parse_size(size_str: str) -> int:
    size_str = size_str.strip()
    for unit, multiplier in sorted(_SIZE_UNITS.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(unit):
            num_part = size_str[: -len(unit)].strip()
            try:
                return int(num_part) * multiplier
            except ValueError:
                raise ValueError(f"无法解析大小: {size_str!r}")
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"无法解析大小: {size_str!r}")


def generate_next_suffix(counter: int, length: int, numeric: bool) -> str:
    if numeric:
        return str(counter).zfill(length)
    result: list[str] = []
    remaining = counter
    digits = []
    if remaining == 0:
        digits.append(0)
    while remaining > 0:
        digits.append(remaining % 26)
        remaining //= 26
    digits = digits[::-1]
    while len(digits) < length:
        digits.insert(0, 0)
    for d in digits:
        result.append(chr(ord("a") + d))
    return "".join(result)


def split_file(config: SplitConfig) -> int:
    if config.lines_per_chunk is not None:
        return _split_by_lines(config)
    elif config.max_bytes_per_chunk is not None:
        return _split_by_size(config)
    else:
        raise ValueError("必须指定 lines_per_chunk 或 max_bytes_per_chunk")


def _split_by_lines(config: SplitConfig) -> int:
    chunk_index = 0
    path_prefix = Path(config.output_prefix)
    current_file: Path | None = None
    current_writer = None
    line_count = 0

    try:
        with config.input_path.open(encoding=config.encoding) as reader:
            for line in reader:
                if line_count == 0:
                    suffix = generate_next_suffix(
                        config.numbering_start + chunk_index,
                        config.suffix_length,
                        config.numeric_suffix,
                    )
                    current_file = path_prefix.with_name(path_prefix.name + suffix)
                    current_writer = current_file.open("w", encoding=config.encoding)
                    chunk_index += 1

                current_writer.write(line)
                line_count += 1

                if line_count >= config.lines_per_chunk:
                    current_writer.close()
                    current_writer = None
                    current_file = None
                    line_count = 0

            if current_writer is not None:
                current_writer.close()
    finally:
        if current_writer is not None:
            current_writer.close()

    return chunk_index


def _split_by_size(config: SplitConfig) -> int:
    chunk_index = 0
    path_prefix = Path(config.output_prefix)
    current_file: Path | None = None
    current_writer = None
    current_bytes = 0

    try:
        with config.input_path.open(encoding=config.encoding) as reader:
            for line in reader:
                line_bytes = len(line.encode(config.encoding))

                if current_writer is None:
                    suffix = generate_next_suffix(
                        config.numbering_start + chunk_index,
                        config.suffix_length,
                        config.numeric_suffix,
                    )
                    current_file = path_prefix.with_name(path_prefix.name + suffix)
                    current_writer = current_file.open("w", encoding=config.encoding)
                    chunk_index += 1
                    current_bytes = 0

                if current_bytes + line_bytes > config.max_bytes_per_chunk and current_bytes > 0:
                    current_writer.close()
                    current_writer = None
                    current_file = None
                    current_bytes = 0

                    suffix = generate_next_suffix(
                        config.numbering_start + chunk_index,
                        config.suffix_length,
                        config.numeric_suffix,
                    )
                    current_file = path_prefix.with_name(path_prefix.name + suffix)
                    current_writer = current_file.open("w", encoding=config.encoding)
                    chunk_index += 1

                current_writer.write(line)
                current_bytes += line_bytes

            if current_writer is not None:
                current_writer.close()
    finally:
        if current_writer is not None:
            current_writer.close()

    return chunk_index
