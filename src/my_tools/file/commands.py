import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click

from ..core.console import confirm, error, notice, warn
from .concat import concatenate_files
from .csv_render import DEFAULT_TEMPLATE, convert_csv
from .excel_csv import list_sheet_names, write_excel_sheet_to_csv
from .json_tools import (
    compact_json,
    escape_json_text,
    pretty_json,
    unescape_json_text,
)

_USER_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "my-tools")


@click.group(name="file")
def file_group():
    """文件工具。"""


@file_group.command("new-with-template")
@click.option("-t", "--template", "template_path", default=None, help="模板文件路径")
@click.option("-f", "--force", is_flag=True, help="强制覆盖已存在的文件")
@click.argument("files", nargs=-1, required=True)
def new_with_template(template_path, force, files):
    """根据模板文件生成新文件。"""
    if template_path is None:
        env_val = os.environ.get("MY_TOOLS_TEMPLATE")
        if env_val:
            template_path = env_val
        else:
            candidates = [
                os.path.join(_USER_CONFIG_DIR, "file-template"),
                os.path.join(os.getcwd(), ".run", "file-template"),
            ]
            for c in candidates:
                if os.path.isfile(c):
                    template_path = c
                    break
            if template_path is None:
                error("未找到默认模板文件，请通过 --template 指定，或创建 ~/.config/my-tools/file-template")

    notice(f"1)解析模板文件 {template_path}")
    if not os.path.isfile(template_path):
        error(f"模板文件不存在 {template_path}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(template_path, encoding="utf-8") as f:
        template_content = f.read()

    notice("2)生成文件:")
    for file_path in files:
        target = Path(file_path)
        if target.exists():
            if force:
                target.unlink()
            else:
                if not confirm(f"文件 {file_path} 已存在，是否删除?", default=False):
                    continue
                target.unlink()

        content = template_content.replace("{{NOW_TIME}}", now)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"    {file_path}")

    notice("完成!")


@file_group.command("zip")
@click.argument("dirs", nargs=-1, required=True)
def zip_dirs(dirs):
    """压缩文件夹，排除 .DS_Store 和 __MACOSX。"""
    for dir_path in dirs:
        if not os.path.isdir(dir_path):
            warn(f"目录不存在 {dir_path}")
            continue

        zip_path = f"{dir_path}.zip"
        if os.path.exists(zip_path):
            if not confirm(f"是否删除已存在的 {zip_path}?", default=False):
                continue
            os.unlink(zip_path)

        subprocess.run([
            "zip", "-x", "*.DS_Store", "-x", "__MACOSX", "-r", zip_path, dir_path
        ], check=True)

    notice("完成!")


@file_group.command("csv-render")
@click.argument(
    "csv_file", required=False, type=click.Path(exists=True, dir_okay=False)
)
@click.option(
    "-o", "--output", type=click.Path(dir_okay=False), help="输出文件路径"
)
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
@click.option(
    "-f",
    "--format",
    "template",
    default=DEFAULT_TEMPLATE,
    show_default=True,
    help="输出模板，变量直接使用 CSV 表头，如 {@timestamp}、{message}",
)
@click.option("--strict", is_flag=True, help="解析异常时返回错误")
def csv_render(csv_file, output, encoding, template, strict):
    """按模板将 CSV 渲染为文本。"""
    if csv_file:
        text = Path(csv_file).read_text(encoding=encoding)
    else:
        text = sys.stdin.read()

    try:
        result = convert_csv(text, template=template, strict=strict)
    except ValueError as e:
        raise click.ClickException(str(e))

    for warning in result.warnings:
        click.echo(f"Warning: {warning}", err=True)

    content = "\n".join(result.lines)
    if content:
        content += "\n"

    if output:
        Path(output).write_text(content, encoding=encoding)
    else:
        click.echo(content, nl=False)


@file_group.command("concat")
@click.argument("paths", nargs=-1, required=True)
@click.option(
    "-o", "--output", type=click.Path(dir_okay=False), help="输出文件路径"
)
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
@click.option(
    "--separator",
    default="",
    show_default=True,
    help="文件之间的分隔符",
)
@click.option("--skip-empty", is_flag=True, help="跳过空文件")
@click.option(
    "--skip-hidden/--no-skip-hidden",
    default=True,
    help="默认跳过隐藏文件（以 . 开头），--no-skip-hidden 关闭",
)
@click.option(
    "--ext",
    "extensions",
    multiple=True,
    default=None,
    help="只拼接指定扩展名的文件，可多次指定，如 --ext .txt --ext .md",
)
def concat(paths, output, encoding, separator, skip_empty, skip_hidden, extensions):
    """按顺序拼接多个文件或目录中的文件。"""
    try:
        result = concatenate_files(
            list(paths),
            encoding=encoding,
            skip_empty=skip_empty,
            skip_hidden=skip_hidden,
            extensions=extensions or None,
            separator=separator,
        )
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        raise click.ClickException(str(e))

    if output:
        Path(output).write_text(result, encoding=encoding)
    else:
        click.echo(result, nl=False)


@file_group.command("excel-to-csv")
@click.argument("excel_file", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output", type=click.Path(dir_okay=False), help="CSV 输出文件路径")
@click.option("--encoding", default="utf-8", show_default=True, help="CSV 输出文件编码")
@click.option("--delimiter", default=",", show_default=True, help="CSV 分隔符")
@click.option("--sheet", help="工作表名称")
@click.option("--sheet-index", type=int, help="工作表序号，1-based")
@click.option("--list-sheets", is_flag=True, help="列出工作表名称后退出")
@click.option("--empty", default="", show_default=True, help="空单元格输出值")
@click.option("--date-format", default="iso", show_default=True, help="日期/时间格式，iso 或 strftime 格式")
@click.option("--formula", is_flag=True, help="输出公式文本而不是公式缓存值")
@click.option("--trim-trailing-empty", is_flag=True, help="裁剪每行尾部空单元格")
def excel_to_csv(
    excel_file,
    output,
    encoding,
    delimiter,
    sheet,
    sheet_index,
    list_sheets,
    empty,
    date_format,
    formula,
    trim_trailing_empty,
):
    """将 Excel 工作表转换为 CSV。"""
    if list_sheets:
        names = list_sheet_names(excel_file)
        for name in names:
            click.echo(name)
        return

    try:
        if output:
            with open(output, "w", encoding=encoding, newline="") as f:
                write_excel_sheet_to_csv(
                    excel_file, f,
                    sheet=sheet,
                    sheet_index=sheet_index,
                    delimiter=delimiter,
                    empty=empty,
                    date_format=date_format,
                    data_only=not formula,
                    trim_trailing_empty_flag=trim_trailing_empty,
                )
        else:
            write_excel_sheet_to_csv(
                excel_file, sys.stdout,
                sheet=sheet,
                sheet_index=sheet_index,
                delimiter=delimiter,
                empty=empty,
                date_format=date_format,
                data_only=not formula,
                trim_trailing_empty_flag=trim_trailing_empty,
            )
    except ValueError as e:
        raise click.ClickException(str(e))


def _read_text(input_file: str | None, encoding: str) -> str:
    if input_file:
        return Path(input_file).read_text(encoding=encoding)
    return sys.stdin.read()


def _write_text(content: str, output: str | None, encoding: str) -> None:
    if not content.endswith("\n"):
        content += "\n"
    if output:
        Path(output).write_text(content, encoding=encoding)
    else:
        click.echo(content, nl=False)


@file_group.command("json-pretty")
@click.argument(
    "input_file", required=False, type=click.Path(exists=True, dir_okay=False)
)
@click.option(
    "-o", "--output", type=click.Path(dir_okay=False), help="输出文件路径"
)
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
@click.option("--indent", default=2, show_default=True, type=int, help="缩进空格数")
@click.option("--sort-keys", is_flag=True, help="按 key 排序")
@click.option("--ascii", "ensure_ascii", is_flag=True, help="转义非 ASCII 字符")
def json_pretty(input_file, output, encoding, indent, sort_keys, ensure_ascii):
    """解析合法 JSON 并格式化为多行缩进形式。"""
    text = _read_text(input_file, encoding)
    try:
        result = pretty_json(text, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@file_group.command("json-compact")
@click.argument(
    "input_file", required=False, type=click.Path(exists=True, dir_okay=False)
)
@click.option(
    "-o", "--output", type=click.Path(dir_okay=False), help="输出文件路径"
)
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
@click.option("--sort-keys", is_flag=True, help="按 key 排序")
@click.option("--ascii", "ensure_ascii", is_flag=True, help="转义非 ASCII 字符")
def json_compact(input_file, output, encoding, sort_keys, ensure_ascii):
    """解析合法 JSON 并压缩为无多余空白形式。"""
    text = _read_text(input_file, encoding)
    try:
        result = compact_json(text, sort_keys=sort_keys, ensure_ascii=ensure_ascii)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)


@file_group.command("json-escape")
@click.argument(
    "input_file", required=False, type=click.Path(exists=True, dir_okay=False)
)
@click.option(
    "-o", "--output", type=click.Path(dir_okay=False), help="输出文件路径"
)
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
@click.option("--wrap", is_flag=True, help="输出完整 JSON 字符串字面量，包含外层双引号")
@click.option("--ascii", "ensure_ascii", is_flag=True, help="转义非 ASCII 字符")
def json_escape(input_file, output, encoding, wrap, ensure_ascii):
    """把任意文本转成 JSON 字符串转义内容。"""
    text = _read_text(input_file, encoding)
    result = escape_json_text(text, wrap=wrap, ensure_ascii=ensure_ascii)
    _write_text(result, output, encoding)


@file_group.command("json-unescape")
@click.argument(
    "input_file", required=False, type=click.Path(exists=True, dir_okay=False)
)
@click.option(
    "-o", "--output", type=click.Path(dir_okay=False), help="输出文件路径"
)
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
def json_unescape(input_file, output, encoding):
    """把 JSON 字符串转义内容还原为原始文本。"""
    text = _read_text(input_file, encoding)
    try:
        result = unescape_json_text(text)
    except ValueError as e:
        raise click.ClickException(str(e))
    _write_text(result, output, encoding)
