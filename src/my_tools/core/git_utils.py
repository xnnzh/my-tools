from .process import capture, run


def current_branch() -> str:
    return capture(["git", "symbolic-ref", "--short", "-q", "HEAD"])


def remote_url() -> str:
    return capture(["git", "remote", "get-url", "origin"])


def remote_branch(branch: str | None = None) -> str:
    ref = f"{branch}@{{u}}" if branch else "HEAD@{u}"
    try:
        return capture(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", ref])
    except Exception:
        return ""


def branch_exists_remote(branch: str) -> bool:
    result = run(["git", "ls-remote", "--exit-code", "--heads", "origin", branch], check=False)
    return result.returncode == 0
