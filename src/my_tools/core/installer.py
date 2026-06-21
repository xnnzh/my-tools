import os
import subprocess

from .console import error, notice
from .process import run

_PROJECT_ROOT: str | None = None


def _find_project_root() -> str:
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT
    env = os.environ.get("MY_TOOLS_HOME")
    if env:
        if not os.path.isdir(env):
            error(f"MY_TOOLS_HOME 指向的目录不存在: {env}")
        _PROJECT_ROOT = os.path.abspath(env)
        return _PROJECT_ROOT
    parent = os.path.abspath(os.getcwd())
    while True:
        pyproject = os.path.join(parent, "pyproject.toml")
        if os.path.isfile(pyproject):
            with open(pyproject) as f:
                if 'name = "my-tools"' in f.read():
                    _PROJECT_ROOT = parent
                    return _PROJECT_ROOT
        next_parent = os.path.dirname(parent)
        if next_parent == parent:
            break
        parent = next_parent
    error(
        "无法定位 my-tools 项目目录，请在项目目录下执行，或设置 MY_TOOLS_HOME 环境变量"
    )


def ensure_clean_or_warn():
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=_find_project_root()
    )
    if result.stdout.strip():
        error("工作区不干净，请先提交或暂存改动。")


def cleanup_legacy_shell_rc():
    home = os.path.expanduser("~")
    marker = "#MY-TOOLS-PATH DO NOT REMOVE THIS COMMENT"
    for rc in (".zshrc", ".bashrc"):
        path = os.path.join(home, rc)
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            lines = f.readlines()
        filtered = [line for line in lines if marker not in line]
        if len(filtered) != len(lines):
            with open(path, "w") as f:
                f.writelines(filtered)
            notice(f"已清理 {rc} 中的旧 marker")


def _install_tool(root: str, *, force_reinstall: bool = False):
    if force_reinstall:
        run(["uv", "tool", "upgrade", "my-tools", "--reinstall", "--directory", root], cwd=root)
    else:
        run(["uv", "tool", "install", ".", "--force"], cwd=root)


def install(force_reinstall: bool = False):
    root = _find_project_root()
    notice("准备安装 my-tools")
    run(["uv", "sync"], cwd=root)
    _install_tool(root, force_reinstall=force_reinstall)
    notice("安装完成，可以使用: my-tools --help")


def uninstall():
    notice("准备卸载 my-tools")
    run(["uv", "tool", "uninstall", "my-tools"], check=False)
    cleanup_legacy_shell_rc()
    notice("卸载完成")


def update(force_reinstall: bool = False):
    root = _find_project_root()
    notice("准备更新 my-tools")
    ensure_clean_or_warn()
    run(["git", "pull", "--ff-only"], cwd=root)
    run(["uv", "sync"], cwd=root)
    _install_tool(root, force_reinstall=force_reinstall)
    notice("更新完成")


def list_tools():
    print("""my-tools install
my-tools uninstall
my-tools update
my-tools list

my-tools git auto
my-tools git new-branch
my-tools git delete-branch
my-tools git open-remote
my-tools git gitlab-merge-request
my-tools git copy-change

my-tools file new-with-template
my-tools file zip

my-tools maven simple

my-tools db batch-delete
my-tools db mybatis-sql
my-tools db insert-sql-to-csv""")
