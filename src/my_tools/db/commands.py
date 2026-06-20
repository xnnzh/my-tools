import click

from .batch_delete import run_batch_delete


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
