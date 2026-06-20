import click

from .core.installer import install, list_tools, uninstall, update
from .db.commands import db
from .file.commands import file_group
from .git.commands import git
from .maven.commands import maven


@click.group()
def cli():
    """my-tools: 个人命令行工具集。"""


cli.add_command(db)
cli.add_command(git)
cli.add_command(file_group, name="file")
cli.add_command(maven)


@cli.command("install")
def install_cmd():
    """安装 my-tools。"""
    install()


@cli.command("uninstall")
def uninstall_cmd():
    """卸载 my-tools。"""
    uninstall()


@cli.command("update")
def update_cmd():
    """更新 my-tools。"""
    update()


@cli.command("list")
def list_cmd():
    """列出可用工具。"""
    list_tools()
