import sys
from pathlib import Path

import click

from .batch_delete import run_batch_delete
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
