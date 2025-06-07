# 代码漏洞风险检查软件 (Code Vulnerability Scanner)

基于大语言模型的代码漏洞风险检查工具，支持多种编程语言和检查模式，为开发者提供全面的代码安全评估解决方案。

> 🤖 **AI辅助开发**：本项目由AI辅助开发，利用大语言模型技术协助设计架构、编写代码和优化界面，展示了AI与人类开发者协作的强大潜力。

## 功能特点

1. **多语言支持**：支持Python、C/C++、Java、JavaScript、Go、Rust等多种编程语言的代码检查
2. **大模型分析**：利用大语言模型进行深度代码分析，发现潜在漏洞和安全风险
3. **项目信息统计**：分析项目结构、代码行数、主要语言分布等信息
4. **多模式检查**：支持单文件、整个项目或Git仓库的检查
5. **GUI和命令行**：同时提供图形界面和命令行接口，满足不同使用场景
6. **Git版本检查**：支持在版本合并前进行安全检查，防止引入新的安全问题
7. **自定义大模型**：支持OpenAI、DeepSeek、Anthropic等多种模型，也可自定义模型
8. **漏洞库更新**：定期更新漏洞知识库，提高检测能力
9. **多格式报告**：支持HTML、JSON和文本格式的详细漏洞报告
10. **严重级别分类**：将发现的漏洞按严重程度分为关键、高、中、低、信息五个级别
11. **自定义规则**：支持用户自定义漏洞检测规则和模式，包括Semgrep规则集成
12. **数据可视化**：直观展示漏洞分布、严重性统计和项目结构

## AI驱动的核心技术

本项目充分利用大语言模型的强大能力，实现了以下创新功能：

1. **语义理解**：不仅识别代码模式，还能理解代码语义和上下文关系
2. **跨文件分析**：分析代码间的依赖关系，发现跨文件安全问题
3. **漏洞解释**：详细解释发现的漏洞，包括成因、影响和修复方法
4. **智能建议**：提供针对性的代码修复建议和最佳实践推荐
5. **自动更新**：漏洞库通过AI技术持续学习最新安全威胁

## 系统要求

- **操作系统**：Windows 10+、macOS 10.14+、Ubuntu 18.04+或其他主流Linux发行版
- **Python版本**：Python 3.8或更高版本
- **硬件要求**：
  - 至少4GB可用RAM
  - 2GB可用磁盘空间
  - 网络连接（用于API调用和漏洞库更新）
- **外部依赖**：
  - 图形界面需要PyQt5支持
  - 报告生成功能需要相关库支持

## 安装方法

### 从源代码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/code-vulnerability-scanner.git
cd code-vulnerability-scanner

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置API密钥（首次运行）
python -m codescan config --api-key YOUR_API_KEY
```

### 使用pip安装（未来支持）

```bash
pip install code-vulnerability-scanner
```

## 环境配置

### API配置

工具需要配置大语言模型API才能正常工作：

```bash
# 配置DeepSeek API
python -m codescan config --api-provider deepseek --api-key YOUR_DEEPSEEK_API_KEY

# 配置OpenAI API
python -m codescan config --api-provider openai --api-key YOUR_OPENAI_API_KEY --api-base https://api.openai.com

# 配置代理（如果需要）
python -m codescan config --proxy http://your-proxy:port
```

### 漏洞库更新

```bash
# 更新内置漏洞库
python -m codescan update

# 从GitHub导入Semgrep规则
python -m codescan import-github --repo-url https://github.com/returntocorp/semgrep-rules --branch main
```

## 使用方法

### 图形界面

启动图形界面进行交互式操作：

```bash
python -m codescan gui
```

### 命令行

```bash
# 扫描单个文件
python -m codescan file /path/to/your/file.py

# 扫描整个目录
python -m codescan dir /path/to/your/project

# 扫描GitHub仓库
python -m codescan github https://github.com/username/repo

# 进行Git合并前检查
python -m codescan git-merge branch_name

# 使用特定模型进行扫描
python -m codescan dir /path/to/project --model anthropic

# 生成特定格式的报告
python -m codescan dir /path/to/project --report-format html

# 排除特定目录或文件
python -m codescan dir /path/to/project --exclude "node_modules,*.tmp,backup/*"

# 显示详细日志
python -m codescan dir /path/to/project --verbose
```

## 扫描结果解读

扫描完成后，将生成包含以下内容的报告：

1. **项目概览**：代码行数、文件数量、语言分布、项目类型识别
2. **漏洞摘要**：按严重级别统计的漏洞数量和分布
3. **详细漏洞列表**：
   - 漏洞类型和分类（如SQL注入、XSS、CSRF等）
   - 严重级别和影响程度
   - 文件位置和行号
   - 问题描述和安全风险
   - 修复建议和最佳实践
   - CWE/OWASP分类参考
4. **安全评分**：基于发现的漏洞给出的总体安全评分
5. **代码质量建议**：除安全问题外的代码质量改进建议

## 规则系统

该工具使用多种规则来检测漏洞：

1. **内置规则**：根据常见漏洞类型预定义的规则
2. **AI模型规则**：由大语言模型动态生成的上下文感知规则
3. **Semgrep规则**：支持导入和使用Semgrep格式的规则
4. **自定义规则**：用户可以在`~/.codescan/rules`目录中添加自定义规则

查看[规则编写指南](docs/rules_guide.md)了解如何创建自定义规则。

## 界面功能亮点

### 现代化GUI设计

- **直观操作**：简洁明了的界面布局，易于上手
- **动态进度条**：实时显示扫描进度
- **可视化图表**：饼图和柱状图展示漏洞分布和严重性
- **科技感主题**：专业的蓝色主题设计，提供舒适的视觉体验
- **可调整布局**：灵活的分割器设计，可根据需要调整面板大小

### 详细报告视图

- **多标签页设计**：项目信息、漏洞列表、详细信息分类展示
- **语法高亮**：代码片段带有语法高亮，易于阅读
- **一键导出**：支持多种格式导出详细报告

## 常见问题与故障排除

### API连接问题

如果遇到API连接问题，请检查：

1. API密钥是否正确配置
2. 网络连接是否正常
3. 是否需要配置代理
4. API服务提供商是否有访问限制

```bash
# 测试API连接
python -m codescan config --test-connection
```

### 扫描速度过慢

1. 考虑使用`--exclude`参数排除不需要扫描的目录
2. 对于大型项目，可以先扫描核心代码目录
3. 检查网络连接和API响应速度

### GUI界面无法启动

1. 确保已安装PyQt5
2. 检查Python版本兼容性
3. 在命令行中运行并查看错误信息

```bash
# 安装GUI依赖
pip install PyQt5
```

## 项目结构

```
codescan/
├── __init__.py        # 包初始化
├── __main__.py        # 入口点
├── cli.py             # 命令行接口
├── gui.py             # 图形界面
├── scanner.py         # 核心扫描引擎
├── models.py          # 大语言模型接口
├── vulndb.py          # 漏洞数据库
├── config.py          # 配置管理
├── report.py          # 报告生成器
├── rule_manager.py    # 规则管理
├── utils.py           # 工具函数
└── styles.py          # 界面样式定义
```

## 开发者文档

详细的技术文档可在docs目录中找到：

- [技术架构文档](docs/technical_doc.md) - 系统架构和实现细节
- [规则编写指南](docs/rules_guide.md) - 如何创建自定义漏洞检测规则
- [贡献指南](docs/CONTRIBUTING.md) - 如何参与项目开发

## 问题反馈

如遇到问题或有改进建议，请通过以下方式反馈：

1. 提交GitHub Issue
2. 发送邮件至support@codescan.example.com
3. 在官方论坛发帖讨论

## 贡献

欢迎提交Pull Request或Issue来帮助改进此项目！查看[贡献指南](docs/CONTRIBUTING.md)了解详情。

## 许可证

本项目采用MIT许可证，详情请查看[LICENSE](LICENSE)文件。 