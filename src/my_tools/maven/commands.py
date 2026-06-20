import click

from ..core.process import run


@click.group()
def maven():
    """Maven 工具。"""


@maven.command(
    "simple",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.pass_context
def simple(ctx):
    """执行 Maven 命令，跳过单元测试和文档。"""
    args = list(ctx.args)
    if not args:
        raise click.UsageError("缺少 Maven 命令参数")
    run([
        "mvn",
        *args,
        "-DskipTests=true",
        "-Dmaven.javadoc.skip=true",
        "-Dmaven.springboot.skip=true",
    ])
