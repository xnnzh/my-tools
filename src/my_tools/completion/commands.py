from pathlib import Path

import click
from click.shell_completion import get_completion_class

from ..core.console import notice, warn


def _completion_source(shell: str) -> str:
    from ..cli import cli

    shell_cls = get_completion_class(shell)
    if shell_cls is None:
        raise click.BadParameter(f"不支持的 shell: {shell}", param_hint="--shell")
    completer = shell_cls(cli, {}, "my-tools", "_MY_TOOLS_COMPLETE")
    return completer.source()


@click.group()
def completion():
    """Shell 命令补全。"""


@completion.command("show")
@click.option("--shell", required=True, type=click.Choice(["zsh", "bash", "fish"]), help="Shell 类型")
def show(shell):
    """输出补全脚本。"""
    click.echo(_completion_source(shell), nl=False)


@completion.command("install")
@click.option("--shell", required=True, type=click.Choice(["zsh", "bash", "fish"]), help="Shell 类型")
def install(shell):
    """安装补全脚本。"""
    source = _completion_source(shell)
    if shell == "fish":
        target = Path.home() / ".config" / "fish" / "completions" / "my-tools.fish"
        target.parent.mkdir(parents=True, exist_ok=True)
    else:
        target = Path.home() / ".config" / "my-tools" / "completions" / f"my-tools.{shell}"
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    notice(f"补全脚本已安装: {target}")
    if shell == "fish":
        notice("Fish 会自动加载补全，重启终端或执行 `exec fish` 即可生效。")
    else:
        rc = {"zsh": "~/.zshrc", "bash": "~/.bashrc"}[shell]
        warn(f"请手动将以下内容加入 {rc}：")
        click.echo(f"  source {target}")
