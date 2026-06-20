import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import click

from ..core.completion import complete_git_branches
from ..core.console import confirm, error, notice, warn
from ..core.git_utils import branch_exists_remote, current_branch, remote_branch, remote_url
from ..core.platform import open_url
from ..core.process import capture, run


@click.group()
def git():
    """Git 工具。"""


@git.command("new-branch")
@click.option("-b", "--branch", "branch_name", required=True, help="新分支名")
def new_branch(branch_name):
    """基于当前分支创建新分支，并与对应的远程分支绑定。"""
    current = current_branch()
    notice(f"1)[{current} ==> {branch_name}]: git checkout -b {branch_name}")
    run(["git", "checkout", "-b", branch_name])
    notice(f"2) git push --set-upstream origin {branch_name}")
    run(["git", "push", "--set-upstream", "origin", branch_name])
    notice("完成!")


@git.command("delete-branch")
@click.argument("branches", nargs=-1, required=True, shell_complete=complete_git_branches)
def delete_branch(branches):
    """删除指定的本地分支和对应的远程分支。"""
    run(["git", "fetch"], check=False)

    local_branches = []
    remote_branches = []

    for b in branches:
        result = run(["git", "show-ref", "--quiet", "refs/heads/" + b], check=False)
        if result.returncode == 0:
            local_branches.append(b)
            rb = remote_branch(b)
            if rb:
                remote_branches.append(rb.removeprefix("origin/"))
            elif branch_exists_remote(b):
                remote_branches.append(b)
        elif branch_exists_remote(b):
            remote_branches.append(b)

    if local_branches:
        notice(f"删除本地分支: git branch -D {' '.join(local_branches)}")
        run(["git", "branch", "-D", *local_branches])

    if remote_branches:
        notice(f"删除远程分支: git push origin --delete {' '.join(remote_branches)}")
        run(["git", "push", "origin", "--delete", *remote_branches])

    notice("完成!")


@git.command("open-remote")
def open_remote():
    """在浏览器打开仓库远程地址。"""
    url = remote_url()
    url = url.removesuffix(".git")
    notice(f"Remote URL: {url}")
    open_url(url)


@git.command("gitlab-merge-request")
@click.option("-r", "--remote-url", "remote", default=None, help="远程仓库地址")
@click.option("-s", "--source-branch", "source", default=None, help="合并请求的源分支")
@click.option("-t", "--target-branch", "target", default=None, help="合并请求的目标分支")
@click.option("--browser", default=None, help="浏览器命令")
def gitlab_merge_request(remote, source, target, browser):
    """提交 GitLab 合并请求。"""
    if remote is None:
        remote = remote_url()
    if source is None:
        source = current_branch()

    if not remote or not source or not target:
        home_url = remote_url()
        url = f"{home_url.removesuffix('.git')}/merge_requests"
        if browser:
            run([browser, url], check=False)
        else:
            open_url(url)
        error("缺少必要参数 --remote-url, --source-branch, --target-branch", exit_code=1)

    merge_url = (
        f"{remote.removesuffix('.git')}/merge_requests/new"
        f"?merge_request%5Bsource_branch%5D={quote(source, safe='')}"
        f"&merge_request%5Btarget_branch%5D={quote(target, safe='')}"
    )
    notice(f"创建合并请求: {merge_url}")
    if browser:
        run([browser, merge_url], check=False)
    else:
        open_url(merge_url)
    notice("完成!")


@git.command("copy-change")
@click.argument("sha1")
@click.argument("sha2")
@click.option("-t", "--target-dir", required=True, help="复制的目标目录")
def copy_change(sha1, sha2, target_dir):
    """复制两次提交之间变更过的文件。"""
    files_str = capture(["git", "diff", "--name-only", sha1, sha2])
    if not files_str:
        notice("没有变更文件")
        return

    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    for file_path in files_str.splitlines():
        src = Path(file_path)
        dst = target_path / src
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        print(f"  {file_path}")

    notice("完成!")


@git.command("auto")
@click.option("-m", "commit_msg", default=None, help="提交信息")
def auto(commit_msg):
    """提交当前分支的变更，并推送到远程。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    notice(f"Time: {now}")
    notice(f"User: {capture(['git', 'config', 'user.name'])}")
    notice(f"Email: {capture(['git', 'config', 'user.email'])}")
    notice(f"Remote: {capture(['git', 'remote', 'get-url', 'origin'])}")

    warn("git fetch")
    run(["git", "fetch", "origin", "--prune"])

    branch = current_branch()
    rbranch = remote_branch()
    notice(f"Current branch: {branch} ==> {rbranch or '[no remote branch]'}")

    warn("git status")
    run(["git", "status"])

    status_out = capture(["git", "status", "--porcelain"])
    change_count = len([line for line in status_out.splitlines() if line.strip()]) if status_out else 0
    stash_list = capture(["git", "stash", "list"], check=False)
    stash_count = len(stash_list.splitlines()) if stash_list else 0
    change_stash = False

    if change_count > 0:
        if confirm("git add .", default=True):
            run(["git", "add", "."])
            if confirm("git commit", default=True):
                if not commit_msg:
                    commit_msg_input = input("请输入提交信息(不输入将使用默认提交信息): ")
                    if not commit_msg_input:
                        commit_msg_input = f"Update changes {now}"
                else:
                    commit_msg_input = commit_msg
                run(["git", "commit", "-m", commit_msg_input])
            else:
                notice("Completed!")
                return
        else:
            change_stash = True

    if not rbranch:
        notice("Completed!")
        return

    if change_stash:
        run(["git", "stash"])

    behind = int(capture(["git", "rev-list", "--count", "HEAD..@{u}"], check=False) or 0)
    if behind > 0:
        warn("git pull --rebase")
        run(["git", "pull", "--rebase"])

    ahead = int(capture(["git", "rev-list", "--count", "@{u}..HEAD"], check=False) or 0)
    if ahead > 0:
        warn("git push")
        run(["git", "push"])

    if change_stash:
        new_stash_list = capture(["git", "stash", "list"], check=False)
        new_stash_count = len(new_stash_list.splitlines()) if new_stash_list else 0
        if stash_count != new_stash_count:
            run(["git", "stash", "pop"])

    notice("Completed!")
