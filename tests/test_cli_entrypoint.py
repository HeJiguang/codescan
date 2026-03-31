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
    assert "usage:" in result.stdout.lower()
    assert "config" in result.stdout
    assert "gui" in result.stdout
    assert "mcp" in result.stdout


def test_config_show_command_is_supported() -> None:
    result = run_codescan("config", "--show")

    assert result.returncode == 0, result.stderr
    assert "API" in result.stdout


def test_mcp_subcommand_help_is_available() -> None:
    result = run_codescan("mcp", "--help")

    assert result.returncode == 0, result.stderr
    assert "--transport" in result.stdout
    assert "stdio" in result.stdout
