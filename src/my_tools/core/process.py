import subprocess


def run(args: list[str], *, cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=check)


def capture(args: list[str], *, cwd: str | None = None, check: bool = True) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()
