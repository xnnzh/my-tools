import sys
from pathlib import Path

import click

from .case_tools import convert_case
from .codec_tools import (
    _check_invalid_percent,
    decode_base_text,
    decode_unicode_text,
    decode_url_text,
    decode_utf8_text,
    encode_base_text,
    encode_unicode_text,
    encode_url_text,
    encode_utf8_text,
)
from .wrap import wrap_lines


def _read_text(text_or_file: str | None, *, from_file: bool, encoding: str) -> str:
    if from_file:
        if not text_or_file:
            raise click.ClickException("使用 --file 时必须提供文件路径")
        return Path(text_or_file).read_text(encoding=encoding)
    if text_or_file is not None:
        return text_or_file
    return sys.stdin.read()


def _write_text(content: str, output: str | None, encoding: str) -> None:
    if not content.endswith("\n"):
        content += "\n"
    if output:
        Path(output).write_text(content, encoding=encoding)
    else:
        click.echo(content, nl=False)


@click.group(name="text")
def text_group():
    """文本处理工具。"""


def _input_output_options(f):
    f = click.option(
        "-f", "--file", "from_file", is_flag=True, help="将输入参数作为文件路径读取"
    )(f)
    f = click.option(
        "-o", "--output", type=click.Path(dir_okay=False), help="输出文件路径"
    )(f)
    f = click.option(
        "--encoding",
        default="utf-8",
        show_default=True,
        help="输入/输出文件编码",
    )(f)
    return f


def _base_option(f):
    f = click.option(
        "--base",
        type=click.Choice(["16", "32", "64", "85"]),
        default="64",
        show_default=True,
        help="Base 编码类型",
    )(f)
    return f


@text_group.command("unicode-encode")
@click.argument("text_or_file", required=False)
@_input_output_options
def unicode_encode(text_or_file, from_file, output, encoding):
    """将非 ASCII 字符转为 \\uXXXX 编码。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    result = encode_unicode_text(text)
    _write_text(result, output, encoding)


@text_group.command("unicode-decode")
@click.argument("text_or_file", required=False)
@_input_output_options
def unicode_decode(text_or_file, from_file, output, encoding):
    """将 \\uXXXX 编码还原为原始文本。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    try:
        result = decode_unicode_text(text)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@text_group.command("utf8-encode")
@click.argument("text_or_file", required=False)
@_input_output_options
def utf8_encode(text_or_file, from_file, output, encoding):
    """将文本编码为 UTF-8 十六进制字节序列。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    try:
        result = encode_utf8_text(text, encoding=encoding)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@text_group.command("utf8-decode")
@click.argument("text_or_file", required=False)
@_input_output_options
def utf8_decode(text_or_file, from_file, output, encoding):
    """将 UTF-8 十六进制字节序列解码为文本。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    try:
        result = decode_utf8_text(text.strip(), encoding=encoding)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@text_group.command("url-encode")
@click.argument("text_or_file", required=False)
@_input_output_options
@click.option(
    "--safe",
    default="",
    show_default=True,
    help="不进行 percent-encoding 的安全字符",
)
@click.option("--plus", is_flag=True, help="空格编码为 +")
def url_encode(text_or_file, from_file, output, encoding, safe, plus):
    """对文本进行 URL percent-encoding 编码。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    result = encode_url_text(text, encoding=encoding, safe=safe, plus=plus)
    _write_text(result, output, encoding)


@text_group.command("url-decode")
@click.argument("text_or_file", required=False)
@_input_output_options
@click.option("--plus", is_flag=True, help="将 + 解码为空格")
def url_decode(text_or_file, from_file, output, encoding, plus):
    """将 URL percent-encoding 解码为原始文本。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    try:
        _check_invalid_percent(text)
        result = decode_url_text(text, encoding=encoding, plus=plus)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@text_group.command("base-encode")
@click.argument("text_or_file", required=False)
@_input_output_options
@_base_option
def base_encode(text_or_file, from_file, output, encoding, base):
    """对文本进行 Base 编码。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    try:
        result = encode_base_text(text, encoding=encoding, base=base)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@text_group.command("base-decode")
@click.argument("text_or_file", required=False)
@_input_output_options
@_base_option
def base_decode(text_or_file, from_file, output, encoding, base):
    """将 Base 编码解码为原始文本。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    try:
        result = decode_base_text(text, encoding=encoding, base=base)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@text_group.command("case")
@click.argument("text_or_file", required=False)
@_input_output_options
@click.option(
    "--to",
    "target_style",
    type=click.Choice(["pascal", "camel", "snake", "kebab", "upper", "lower"]),
    required=True,
    help="目标命名风格",
)
def case(text_or_file, from_file, output, encoding, target_style):
    """按目标风格转换命名。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    try:
        result = convert_case(text, target_style)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@text_group.command("upper")
@click.argument("text_or_file", required=False)
@_input_output_options
def upper(text_or_file, from_file, output, encoding):
    """将文本转换为大写。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    _write_text(text.upper(), output, encoding)


@text_group.command("lower")
@click.argument("text_or_file", required=False)
@_input_output_options
def lower(text_or_file, from_file, output, encoding):
    """将文本转换为小写。"""
    text = _read_text(text_or_file, from_file=from_file, encoding=encoding)
    _write_text(text.lower(), output, encoding)


@text_group.command("wrap")
@click.argument("file", type=click.Path(dir_okay=False, readable=True), required=False)
@click.option("--prefix", required=True, help="前缀，添加到每一行")
@click.option("--suffix", default="", help="后缀，添加到每一行")
@click.option("--last-suffix", default=None, help="最后一行使用的后缀（覆盖 --suffix）")
@click.option("--keep-empty", is_flag=True, help="保留空行，默认跳过空行")
@click.option("-o", "--output", type=click.Path(dir_okay=False), help="输出文件路径")
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
def wrap(file, prefix, suffix, last_suffix, keep_empty, output, encoding):
    """给每行添加前缀和后缀。"""
    if file is not None:
        text = Path(file).read_text(encoding=encoding)
    else:
        import sys
        text = sys.stdin.read()
    result = wrap_lines(
        text,
        prefix,
        suffix=suffix,
        last_suffix=last_suffix,
        keep_empty=keep_empty,
    )
    if not result.endswith("\n"):
        result += "\n"
    if output:
        Path(output).write_text(result, encoding=encoding)
    else:
        click.echo(result, nl=False)
