"""Command-line entry point for CodeScan."""

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
    """Build the package CLI parser."""

    parser = argparse.ArgumentParser(
        description="代码安全扫描工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  扫描单个文件:
    python -m codescan file path/to/file.py

  扫描目录:
    python -m codescan dir path/to/directory

  扫描GitHub仓库:
    python -m codescan github https://github.com/user/repo

  启动GUI界面:
    python -m codescan gui
        """,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="命令")

    config_parser = subparsers.add_parser("config", help="配置工具")
    config_parser.add_argument("--show", action="store_true", help="显示当前配置")
    config_parser.add_argument("--api-key", help="设置API密钥")
    config_parser.add_argument("--model", help="设置模型名称")
    config_parser.add_argument("--base-url", "--api-base", dest="base_url", help="设置API基础URL")
    config_parser.add_argument(
        "--provider",
        "--api-provider",
        dest="provider",
        choices=["openai", "deepseek", "anthropic", "custom"],
        help="设置API提供商",
    )
    config_parser.add_argument("--http-proxy", "--proxy", dest="http_proxy", help="设置HTTP代理")

    scan_file_parser = subparsers.add_parser("file", aliases=["scan-file"], help="扫描单个文件")
    scan_file_parser.add_argument("path", help="文件路径")
    scan_file_parser.add_argument("--output", "-o", help="输出报告路径")
    scan_file_parser.add_argument("--model", "-m", help="使用的模型名称", default="default")

    scan_dir_parser = subparsers.add_parser("dir", aliases=["scan-dir"], help="扫描目录")
    scan_dir_parser.add_argument("path", help="目录路径")
    scan_dir_parser.add_argument("--output", "-o", help="输出报告路径")
    scan_dir_parser.add_argument("--model", "-m", help="使用的模型名称", default="default")
    scan_dir_parser.add_argument("--exclude", "-e", help="排除的文件/目录模式（glob格式）")

    scan_github_parser = subparsers.add_parser(
        "github", aliases=["scan-github"], help="扫描GitHub仓库"
    )
    scan_github_parser.add_argument("url", help="GitHub仓库URL")
    scan_github_parser.add_argument("--output", "-o", help="输出报告路径")
    scan_github_parser.add_argument("--model", "-m", help="使用的模型名称", default="default")

    merge_parser = subparsers.add_parser(
        "git-merge", aliases=["scan-git-merge"], help="扫描Git合并差异"
    )
    merge_parser.add_argument("branch", help="目标分支")
    merge_parser.add_argument("--output", "-o", help="输出报告路径")
    merge_parser.add_argument("--model", "-m", help="使用的模型名称", default="default")

    subparsers.add_parser("update", help="更新漏洞库")

    import_rule_parser = subparsers.add_parser("import-rule", help="从URL导入规则")
    import_rule_parser.add_argument("url", help="规则URL")

    import_github_parser = subparsers.add_parser("import-github", help="从GitHub导入规则")
    import_github_parser.add_argument("--repo-url", required=True, help="GitHub仓库URL")
    import_github_parser.add_argument("--branch", default="main", help="分支名")
    import_github_parser.add_argument("--languages", help="语言列表，使用逗号分隔")

    subparsers.add_parser("gui", help="启动图形界面")

    return parser


def main() -> int:
    """Program entry point."""

    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        if not check_api_config():
            print("\n提示: 您需要先配置API密钥才能使用分析功能。")
            print("请使用以下命令配置API密钥:")
            print("python -m codescan config --api-key YOUR_API_KEY")
        return 0

    if args.command == "gui":
        from PyQt5.QtWidgets import QApplication

        from .gui import main as gui_main
        from .styles import apply_style

        app = QApplication(sys.argv)
        apply_style(app)
        return gui_main(app)

    return cli_main(args)


if __name__ == "__main__":
    sys.exit(main())
