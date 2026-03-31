"""Command-line entry point for CodeScan."""

from __future__ import annotations

import argparse
import sys

from .__init__ import __version__
from .cli import main as cli_main
from .config import config


def check_api_config() -> bool:
    """Check whether a default API key is configured."""

    models_config = config.config.get("models", {})
    default_config = models_config.get("default", {})
    return bool(default_config.get("api_key", ""))


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level package parser."""

    parser = argparse.ArgumentParser(
        description="CodeScan command line interface.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m codescan file path/to/file.py\n"
            "  python -m codescan dir path/to/project\n"
            "  python -m codescan github https://github.com/user/repo\n"
            "  python -m codescan git-merge main\n"
            "  python -m codescan mcp --transport stdio\n"
            "  python -m codescan gui\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    config_parser = subparsers.add_parser("config", help="Manage model configuration")
    config_parser.add_argument("--show", action="store_true", help="Show the current configuration")
    config_parser.add_argument("--api-key", help="Set the API key")
    config_parser.add_argument("--model", help="Set the model name")
    config_parser.add_argument("--base-url", "--api-base", dest="base_url", help="Set the model base URL")
    config_parser.add_argument(
        "--provider",
        "--api-provider",
        dest="provider",
        choices=["openai", "deepseek", "anthropic", "custom"],
        help="Set the model provider",
    )
    config_parser.add_argument("--http-proxy", "--proxy", dest="http_proxy", help="Set the HTTP proxy")

    scan_file_parser = subparsers.add_parser("file", aliases=["scan-file"], help="Scan a single file")
    scan_file_parser.add_argument("path", help="Path to the file")
    scan_file_parser.add_argument("--output", "-o", help="Path for the generated report")
    scan_file_parser.add_argument("--model", "-m", default="default", help="Model name to use")

    scan_dir_parser = subparsers.add_parser("dir", aliases=["scan-dir"], help="Scan a directory")
    scan_dir_parser.add_argument("path", help="Path to the directory")
    scan_dir_parser.add_argument("--output", "-o", help="Path for the generated report")
    scan_dir_parser.add_argument("--model", "-m", default="default", help="Model name to use")
    scan_dir_parser.add_argument("--exclude", "-e", help="Glob pattern to exclude")

    scan_github_parser = subparsers.add_parser(
        "github",
        aliases=["scan-github"],
        help="Scan a GitHub repository by cloning it locally first",
    )
    scan_github_parser.add_argument("url", help="GitHub repository URL")
    scan_github_parser.add_argument("--output", "-o", help="Path for the generated report")
    scan_github_parser.add_argument("--model", "-m", default="default", help="Model name to use")

    merge_parser = subparsers.add_parser(
        "git-merge",
        aliases=["scan-git-merge"],
        help="Scan files changed against a target branch in the current repository",
    )
    merge_parser.add_argument("branch", help="Base branch or ref")
    merge_parser.add_argument("--output", "-o", help="Path for the generated report")
    merge_parser.add_argument("--model", "-m", default="default", help="Model name to use")

    subparsers.add_parser("update", help="Update the vulnerability database")

    import_rule_parser = subparsers.add_parser("import-rule", help="Import rules from a URL")
    import_rule_parser.add_argument("url", help="Rule definition URL")

    import_github_parser = subparsers.add_parser("import-github", help="Import rules from a GitHub repository")
    import_github_parser.add_argument("--repo-url", required=True, help="GitHub repository URL")
    import_github_parser.add_argument("--branch", default="main", help="Branch to import from")
    import_github_parser.add_argument("--languages", help="Comma-separated language filter")

    mcp_parser = subparsers.add_parser("mcp", help="Run the CodeScan MCP server")
    mcp_parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport to expose",
    )
    mcp_parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP transports")
    mcp_parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transports")
    mcp_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Server log level",
    )

    subparsers.add_parser("gui", help="Launch the desktop GUI")

    return parser


def main() -> int:
    """Program entry point."""

    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        if not check_api_config():
            print("\nTip: configure an API key before using the AI analysis flow.")
            print("Run: python -m codescan config --api-key YOUR_API_KEY")
        return 0

    if args.command == "gui":
        from PyQt5.QtWidgets import QApplication

        from .gui import main as gui_main
        from .styles import apply_style

        app = QApplication(sys.argv)
        apply_style(app)
        return gui_main(app)

    if args.command == "mcp":
        from .mcp_server import run_server_from_namespace

        return run_server_from_namespace(args)

    return cli_main(args)


if __name__ == "__main__":
    sys.exit(main())
