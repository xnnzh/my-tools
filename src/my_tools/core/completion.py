from click.shell_completion import CompletionItem

from .process import capture


def complete_git_branches(ctx, param, incomplete):
    try:
        output = capture(["git", "branch", "--format=%(refname:short)"], check=False)
    except Exception:
        return []

    branches = []
    for line in output.splitlines():
        branch = line.strip()
        if not branch or branch == "HEAD":
            continue
        if branch.startswith(incomplete):
            branches.append(CompletionItem(branch))
    return sorted(branches, key=lambda item: item.value)
