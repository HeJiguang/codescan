import os
import subprocess
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(__file__))


def run_codescan(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    python_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = REPO_ROOT if not python_path else REPO_ROOT + os.pathsep + python_path
    return subprocess.run(
        [sys.executable, "-m", "codescan", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_package_help_works_without_gui_import_failure() -> None:
    result = run_codescan("--help")

    assert result.returncode == 0, result.stderr
    assert "代码安全扫描工具" in result.stdout
    assert "gui" in result.stdout


def test_config_show_command_is_supported() -> None:
    result = run_codescan("config", "--show")

    assert result.returncode == 0, result.stderr
    assert "API" in result.stdout
