import sys
from pathlib import Path

import click

from .batch_delete import run_batch_delete
from .csv_insert_sql import (
    convert_csv_to_insert_sql,
    merge_field_types,
    parse_extra_assignment,
    parse_field_list,
    parse_field_types,
)
from .insert_sql_csv import parse_insert_sql, write_csv
from .mybatis_sql import format_mybatis_log


@click.group()
def db():
    """数据库相关工具。"""


@db.command("batch-delete")
@click.argument("config", type=click.Path(exists=True))
@click.option("--task", multiple=True, help="指定要执行的任务 name（可多次）")
@click.option("--list", "list_tasks", is_flag=True, help="仅列出所有可用的任务")
@click.option("--dry-run", is_flag=True, help="Dry-Run 模式：只收集统计，不执行删除")
@click.option("--env", type=click.Path(exists=True), help="加载 .env 文件路径")
@click.option("--log-file", help="日志文件路径（默认 ./app-{PID}.log）")
@click.option("--no-log-file", is_flag=True, help="不写日志文件，仅输出到终端")
def batch_delete(config, task, list_tasks, dry_run, env, log_file, no_log_file):
    """按配置批量删除 MySQL 表数据。"""
    run_batch_delete(
        config_path=config,
        tasks=task,
        list_tasks=list_tasks,
        dry_run=dry_run,
        env_file=env,
        log_file=log_file,
        no_log_file=no_log_file,
    )


@db.command("mybatis-sql")
@click.argument("log_files", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--mode",
    type=click.Choice(["replace", "append", "sql-only"]),
    default="replace",
    show_default=True,
    help="输出模式：替换 SQL 日志、追加转换 SQL、或仅输出 SQL",
)
@click.option("--strict", is_flag=True, help="参数数量不匹配时返回错误")
@click.option("--semicolon/--no-semicolon", default=True, help="SQL 末尾是否补分号")
@click.option(
    "--blank-line/--no-blank-line",
    default=True,
    help="sql-only 模式下多条 SQL 之间是否空行分隔",
)
def mybatis_sql(log_files, mode, strict, semicolon, blank_line):
    """将 MyBatis 日志中的 Preparing / Parameters 转换为可执行的 SQL。"""
    if log_files:
        parts = []
        for f in log_files:
            parts.append(Path(f).read_text(encoding="utf-8"))
        text = "\n".join(parts)
    else:
        text = sys.stdin.read()

    result, warnings = format_mybatis_log(
        text,
        mode=mode,
        semicolon=semicolon,
        blank_line=blank_line,
        strict=strict,
    )

    for w in warnings:
        click.echo(f"Warning: {w}", err=True)

    if strict and warnings:
        raise click.ClickException("处理过程中存在错误")

    click.echo(result, nl=False)


@db.command("insert-sql-to-csv")
@click.argument(
    "sql_file", required=False, type=click.Path(exists=True, dir_okay=False)
)
@click.option(
    "-o", "--output", type=click.Path(dir_okay=False), help="CSV 输出文件路径"
)
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
@click.option(
    "--delimiter",
    default=",",
    show_default=True,
    help="CSV 分隔符",
)
@click.option(
    "--strict",
    is_flag=True,
    help="解析异常时返回错误",
)
def insert_sql_to_csv(sql_file, output, encoding, delimiter, strict):
    """将 INSERT SQL 转换为 CSV，CSV 标题使用 INSERT 中的列名。"""
    if sql_file:
        sql = Path(sql_file).read_text(encoding=encoding)
    else:
        sql = sys.stdin.read()

    try:
        data = parse_insert_sql(sql, strict=strict)
    except ValueError as e:
        raise click.ClickException(str(e))

    for w in data.warnings:
        click.echo(f"Warning: {w}", err=True)

    if strict and data.warnings:
        raise click.ClickException("转换过程中存在警告")

    if output:
        with open(output, "w", encoding=encoding, newline="") as f:
            write_csv(data, f, delimiter=delimiter)
    else:
        write_csv(data, sys.stdout, delimiter=delimiter)


def _flatten_field_options(values: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    for value in values:
        result.extend(parse_field_list(value) or [])
    return result


@db.command("csv-to-insert-sql")
@click.argument("csv_file", required=False, type=click.Path(exists=True, dir_okay=False))
@click.option("-t", "--table", required=True, help="目标表名")
@click.option("-d", "--database", help="数据库名（可选）")
@click.option("--fields", help="要包含的字段列表，逗号分隔（默认使用 CSV 全部字段）")
@click.option("--exclude-fields", help="要排除的字段列表，逗号分隔")
@click.option(
    "--extra",
    multiple=True,
    help="额外字符串字段，格式 name=value（可多次使用）",
)
@click.option(
    "--extra-sql",
    multiple=True,
    help="额外 SQL 表达式字段，格式 name=expr（可多次使用，不添加引号）",
)
@click.option(
    "--field-types",
    help="字段类型映射，格式 name:type,...（type: string/number/boolean/sql/null）",
)
@click.option(
    "--number-fields",
    multiple=True,
    help="标记为数字类型的字段名（逗号分隔或多次使用，不添加引号）",
)
@click.option(
    "--boolean-fields",
    multiple=True,
    help="标记为布尔类型的字段名（逗号分隔或多次使用，输出 TRUE/FALSE）",
)
@click.option(
    "--batch-size",
    default=1000,
    show_default=True,
    help="每个 INSERT 语句包含的最大行数",
)
@click.option(
    "--no-batch",
    is_flag=True,
    help="禁用批量模式，每行生成一个 INSERT",
)
@click.option(
    "-o", "--output", type=click.Path(dir_okay=False), help="SQL 输出文件路径（默认 stdout）"
)
@click.option(
    "--delimiter",
    default=",",
    show_default=True,
    help="CSV 分隔符",
)
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="输入/输出文件编码",
)
@click.option(
    "--strict",
    is_flag=True,
    help="严格模式：警告视为错误",
)
def csv_to_insert_sql(
    csv_file,
    table,
    database,
    fields,
    exclude_fields,
    extra,
    extra_sql,
    field_types,
    number_fields,
    boolean_fields,
    batch_size,
    no_batch,
    output,
    delimiter,
    encoding,
    strict,
):
    """将 CSV 转换为 INSERT SQL。"""
    if csv_file:
        text = Path(csv_file).read_text(encoding=encoding)
    else:
        text = sys.stdin.read()

    try:
        parsed_fields = parse_field_list(fields)
        parsed_exclude = parse_field_list(exclude_fields)
        parsed_extra = [
            parse_extra_assignment(e) for e in extra
        ] + [
            parse_extra_assignment(e, raw_sql=True) for e in extra_sql
        ]
        parsed_types = parse_field_types(field_types) if field_types else {}

        merged_types = merge_field_types(
            field_types=parsed_types,
            number_fields=_flatten_field_options(number_fields),
            boolean_fields=_flatten_field_options(boolean_fields),
            extra_fields=parsed_extra,
        )

        result = convert_csv_to_insert_sql(
            text,
            table=table,
            database=database or None,
            fields=parsed_fields,
            exclude_fields=parsed_exclude,
            extra_fields=parsed_extra,
            field_types=merged_types,
            delimiter=delimiter,
            batch=not no_batch,
            batch_size=batch_size,
            strict=strict,
        )
    except ValueError as e:
        raise click.ClickException(str(e))

    for w in result.warnings:
        click.echo(f"Warning: {w}", err=True)

    if strict and result.warnings:
        raise click.ClickException("转换过程中存在警告")

    if output:
        Path(output).write_text(result.sql, encoding=encoding)
    else:
        click.echo(result.sql, nl=False)
