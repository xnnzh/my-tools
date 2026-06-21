import click

from .completion.commands import completion
from .core.installer import install, list_tools, uninstall, update
from .db.commands import db
from .file.commands import file_group
from .git.commands import git
from .maven.commands import maven
from .text.commands import text_group
from .time_tools.commands import time_group


@click.group()
def cli():
    """my-tools: 个人命令行工具集。"""


cli.add_command(completion)
cli.add_command(db)
cli.add_command(git)
cli.add_command(file_group, name="file")
cli.add_command(maven)
cli.add_command(text_group)
cli.add_command(time_group)


@cli.command("install")
@click.option("--force-reinstall", is_flag=True, help="强制重新构建并重装全局 my-tools")
def install_cmd(force_reinstall):
    """安装 my-tools。"""
    install(force_reinstall=force_reinstall)


@cli.command("uninstall")
def uninstall_cmd():
    """卸载 my-tools。"""
    uninstall()


@cli.command("update")
@click.option("--force-reinstall", is_flag=True, help="更新后强制重新构建并重装全局 my-tools")
def update_cmd(force_reinstall):
    """更新 my-tools。"""
    update(force_reinstall=force_reinstall)


@cli.command("list")
def list_cmd():
    """列出可用工具。"""
    list_tools()
