from unittest.mock import patch

from my_tools.core import installer


def test_install_uses_uv_tool_install_by_default(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-tools"\n', encoding="utf-8")

    with patch.dict("os.environ", {"MY_TOOLS_HOME": str(tmp_path)}), patch.object(installer, "run") as run_mock:
        installer._PROJECT_ROOT = None
        installer.install()

    run_mock.assert_any_call(["uv", "sync"], cwd=str(tmp_path))
    run_mock.assert_any_call(["uv", "tool", "install", ".", "--force"], cwd=str(tmp_path))


def test_install_force_reinstall_uses_uv_tool_upgrade(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-tools"\n', encoding="utf-8")

    with patch.dict("os.environ", {"MY_TOOLS_HOME": str(tmp_path)}), patch.object(installer, "run") as run_mock:
        installer._PROJECT_ROOT = None
        installer.install(force_reinstall=True)

    run_mock.assert_any_call(["uv", "sync"], cwd=str(tmp_path))
    run_mock.assert_any_call(
        ["uv", "tool", "upgrade", "my-tools", "--reinstall", "--directory", str(tmp_path)],
        cwd=str(tmp_path),
    )


def test_update_force_reinstall_uses_uv_tool_upgrade(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-tools"\n', encoding="utf-8")

    with (
        patch.dict("os.environ", {"MY_TOOLS_HOME": str(tmp_path)}),
        patch.object(installer, "run") as run_mock,
        patch.object(installer, "ensure_clean_or_warn"),
    ):
        installer._PROJECT_ROOT = None
        installer.update(force_reinstall=True)

    run_mock.assert_any_call(["git", "pull", "--ff-only"], cwd=str(tmp_path))
    run_mock.assert_any_call(["uv", "sync"], cwd=str(tmp_path))
    run_mock.assert_any_call(
        ["uv", "tool", "upgrade", "my-tools", "--reinstall", "--directory", str(tmp_path)],
        cwd=str(tmp_path),
    )


def test_update_uses_uv_tool_install_by_default(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-tools"\n', encoding="utf-8")

    with (
        patch.dict("os.environ", {"MY_TOOLS_HOME": str(tmp_path)}),
        patch.object(installer, "run") as run_mock,
        patch.object(installer, "ensure_clean_or_warn"),
    ):
        installer._PROJECT_ROOT = None
        installer.update()

    run_mock.assert_any_call(["git", "pull", "--ff-only"], cwd=str(tmp_path))
    run_mock.assert_any_call(["uv", "sync"], cwd=str(tmp_path))
    run_mock.assert_any_call(["uv", "tool", "install", ".", "--force"], cwd=str(tmp_path))
