import os
import platform
import subprocess
import webbrowser


def get_os_name() -> str:
    system = platform.system()
    if system == "Darwin":
        return "Mac"
    if system == "Linux":
        return "Linux"
    if system.startswith("Windows") or os.name == "nt":
        return "Windows"
    return "Other"


def open_url(url: str):
    system = get_os_name()
    if system == "Mac":
        subprocess.run(["open", url], check=False)
    elif system == "Linux":
        subprocess.run(["xdg-open", url], check=False)
    elif system == "Windows":
        webbrowser.open(url)
    else:
        print(url)
