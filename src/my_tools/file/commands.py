import os
import subprocess
from datetime import datetime
from pathlib import Path

import click

from ..core.console import confirm, error, notice, warn

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
