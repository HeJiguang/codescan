# CodeScan

![CI](https://github.com/HeJiguang/codescan/actions/workflows/ci.yml/badge.svg)

面向代码仓库的 AI 安全扫描工具。它结合规则匹配和大模型分析，对单文件、目录、GitHub 仓库和 Git 合并差异做安全检查，并输出 HTML / JSON / 文本报告。

## 现在有什么不一样

当前主线已经不是最早的“长 prompt + 手工抠 JSON”的原型实现，而是：

- `LangChain` 统一模型接入
- `LangGraph` 编排文件级分析流程
- 结构化输出约束扫描结果
- CLI 与 GUI 解耦，命令行帮助不再被 GUI 依赖拖死
- 扫描结果模型和报告层已经对齐

如果你想把它继续打磨成一个更像产品、而不是课程作业的开源项目，这个版本才是可继续演进的起点。

## 适合什么场景

- 在本地快速扫一个可疑文件
- 在提交前扫一遍目录或仓库
- 对 GitHub 仓库做一次轻量级安全体检
- 导入 Semgrep 规则，结合 AI 输出更容易读的解释和建议

## 当前架构

```text
GUI / CLI
   |
scanner.py
   |
codescan/ai/
├── providers.py   -> 统一模型创建
├── prompts.py     -> Prompt 构建
├── chains.py      -> LangChain 结构化输出链
├── workflow.py    -> LangGraph 工作流
├── schemas.py     -> Pydantic 结构化结果
└── service.py     -> 扫描器调用入口
   |
vulndb.py / semgrep_converter.py / report.py
```

## 支持的模型提供方

- DeepSeek
- OpenAI
- Anthropic
- 兼容 OpenAI API 的自定义服务

说明：

- `DeepSeek` 和多数兼容 OpenAI 的服务都通过 `langchain-openai` 接入
- `Anthropic` 依赖 `langchain-anthropic`
- GUI 需要 `PyQt5` 和 `PyQtChart`

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/HeJiguang/codescan.git
cd codescan
```

### 2. 创建环境并安装依赖

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 3. 配置模型

```bash
# 查看当前配置
python -m codescan config --show

# 配置 DeepSeek
python -m codescan config --provider deepseek --api-key YOUR_DEEPSEEK_API_KEY --model deepseek-chat

# 配置 OpenAI
python -m codescan config --provider openai --api-key YOUR_OPENAI_API_KEY --model gpt-4o-mini --base-url https://api.openai.com/v1

# 配置代理
python -m codescan config --http-proxy http://127.0.0.1:7890
```

## 使用方式

### 命令行

```bash
# 扫描单文件
python -m codescan file /path/to/file.py

# 扫描目录
python -m codescan dir /path/to/project

# 扫描 GitHub 仓库
python -m codescan github https://github.com/HeJiguang/codescan.git

# 扫描当前仓库与某分支的差异文件
python -m codescan git-merge main

# 输出 JSON 报告
python -m codescan file /path/to/file.py --output result.json
```

### 图形界面

```bash
python -m codescan gui
```

## 规则系统

CodeScan 目前支持三层能力：

1. 内置规则库
2. Semgrep 规则导入
3. LLM 深度分析

可以通过下面的命令导入规则：

```bash
# 更新漏洞库
python -m codescan update

# 从 URL 导入规则
python -m codescan import-rule https://example.com/rules.yaml

# 从 GitHub 导入 Semgrep 规则
python -m codescan import-github --repo-url https://github.com/returntocorp/semgrep-rules --branch main
```

## 输出结果

扫描结果会统一映射到 `ScanResult` / `VulnerabilityIssue`，报告层支持：

- HTML 报告
- JSON 报告
- 文本报告

当前报告中会包含：

- 扫描对象与模型信息
- 严重级别统计
- 文件位置与代码片段
- 修复建议
- 项目概览或文件概览

## 开发状态

这个项目目前已经完成一轮 AI 运行时重构，但还没有到“最终产品形态”。如果继续维护，我认为最值得做的三件事是：

1. 把 GUI 从单文件巨型模块继续拆分
2. 把规则层从简单正则升级到更可信的 AST / Semgrep 复核流程
3. 增加真正面向开源用户的 demo、样例报告和 benchmark

## 测试

```bash
python -m pytest tests -q
python -m compileall codescan
python -m codescan --help
```

## 文档

- [技术文档](docs/technical_doc.md)
- [文档索引](docs/README.md)
- [规则编写指南](docs/rules_guide.md)
- [贡献指南](docs/CONTRIBUTING.md)

## 许可证

MIT，见 [LICENSE](LICENSE)。
