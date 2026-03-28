# CodeScan 技术文档

## 1. 目标

CodeScan 的目标不是“做一个能聊天的安全 Agent”，而是“做一个可维护的代码安全扫描器”。

因此当前架构有两个核心约束：

1. 产品入口仍然是扫描器，而不是对话系统
2. AI 负责增强分析能力，但不能吞掉规则层、报告层和产品边界

## 2. 当前架构

### 2.1 总览

```text
GUI / CLI
   |
CodeScanner
   |
AIAnalysisService
   |
codescan/ai/
├── providers.py
├── prompts.py
├── chains.py
├── workflow.py
└── schemas.py
   |
VulnerabilityDB / ReportGenerator
```

### 2.2 分层说明

#### 表现层

- `codescan/__main__.py`
- `codescan/cli.py`
- `codescan/gui.py`

职责：

- 接收用户输入
- 组织扫描命令
- 展示扫描结果

约束：

- CLI 不应强依赖 GUI
- GUI 可以依赖扫描器，但不应该实现扫描核心逻辑

#### 应用层

- `codescan/scanner.py`

职责：

- 收集文件
- 处理排除规则
- 组织单文件与目录扫描
- 聚合 `ScanResult`

它是产品主入口，不负责维护 Prompt 细节，也不负责和具体厂商 SDK 深度耦合。

#### AI 运行时层

- `codescan/ai/providers.py`
- `codescan/ai/prompts.py`
- `codescan/ai/chains.py`
- `codescan/ai/workflow.py`
- `codescan/ai/service.py`
- `codescan/ai/schemas.py`

职责：

- 创建模型实例
- 定义结构化输出
- 构建 LangChain 调用链
- 用 LangGraph 组织多步文件分析

这是当前重构的核心。

#### 数据与规则层

- `codescan/vulndb.py`
- `codescan/semgrep_converter.py`
- `codescan/config.py`

职责：

- 规则管理
- 配置管理
- 外部规则导入

#### 输出层

- `codescan/report.py`

职责：

- 将统一的 `ScanResult` 映射为 HTML / JSON / 文本报告

## 3. AI 运行时设计

### 3.1 Providers

`providers.py` 使用 `LangChain` 统一模型创建。

当前策略：

- `openai` / `deepseek` / `custom` 统一按 OpenAI 兼容协议处理
- `anthropic` 作为可选依赖处理

这样做的原因是：

- DeepSeek 与大量兼容 OpenAI 的推理服务都能走同一条通道
- 模型切换不需要让扫描器感知底层 SDK 差异

### 3.2 Schemas

`schemas.py` 使用 `Pydantic` 定义结构化输出：

- `AIFileIssue`
- `AIFileScanResult`
- `AIProjectSummary`
- `AIFileSummary`

这一步解决的是旧实现里最脆弱的问题：

- 模型输出是自由文本
- 结果靠正则或字符串截取做 JSON 提取
- 上层模块不得不猜字段是否存在

### 3.3 Chains

`chains.py` 中的链负责两件事：

1. 绑定 system/human prompt
2. 调用 `with_structured_output(...)`

也就是说，扫描器不再自己拼“请严格返回 JSON”这种巨型提示词。

### 3.4 Workflow

`workflow.py` 中的 LangGraph 工作流当前用于文件级分析。

流程如下：

```text
START
  -> rule_scan
  -> llm_scan
  -> merge_and_finalize
END
```

设计意图：

- 保留规则层价值
- 让 LLM 分析结果和规则结果在统一节点合并
- 以后容易加去重、复核、二次评分、置信度修正

## 4. 扫描流程

### 4.1 单文件扫描

1. 判断文件是否应排除
2. 读取文件内容
3. 根据规则库生成 rule-based issues
4. 调用 `AIAnalysisService.analyze_file(...)`
5. 合并结果并生成 `ScanResult`
6. 再生成文件级摘要

### 4.2 目录扫描

1. 收集文件列表
2. 并发扫描每个文件
3. 聚合统计信息
4. 调用 AI 生成项目摘要
5. 输出统一扫描结果

## 5. 当前主要数据模型

### 5.1 VulnerabilityIssue

位于 `codescan/scanner.py`。

当前关键字段：

- `title`
- `severity`
- `file_path`
- `line_number`
- `description`
- `recommendation`
- `cwe_id`
- `owasp_category`
- `vulnerability_type`
- `confidence`

之所以在领域模型里保留 `owasp_category` / `vulnerability_type`，是因为 GUI 与报告层都可能消费这些字段。即使当前 AI 主流程还没有系统性填充它们，模型本身也必须兼容。

### 5.2 ScanResult

当前关键字段：

- `scan_id`
- `scan_path`
- `scan_type`
- `scan_model`
- `timestamp`
- `issues`
- `stats`
- `project_info`

这让报告层不再需要猜测“扫描模型是不是存在”。

## 6. CLI 设计

当前入口命令：

- `config`
- `file`
- `dir`
- `github`
- `git-merge`
- `update`
- `import-rule`
- `import-github`
- `gui`

兼容别名仍保留：

- `scan-file`
- `scan-dir`
- `scan-github`

重构重点不是换名字，而是修复以下问题：

- parser 定义和 `cli.py` 分发不一致
- CLI 帮助会被 GUI 导入拖死
- config 参数名和处理函数读取的字段名不一致

## 7. 已知问题

这轮重构后，主路径已经可用，但还有几类问题值得继续处理：

1. `gui.py` 仍然过大，维护成本高
2. 规则匹配仍偏轻量，误报控制一般
3. 项目级总结依然高度依赖模型质量
4. 缺少真实样例仓库的 benchmark 和截图

## 8. 建议的下一阶段

如果要把这个项目继续维护成更适合公开发布的仓库，建议按下面顺序推进：

### 阶段一：产品化整理

- 增加示例报告
- 增加截图
- 优化 README 首页叙事

### 阶段二：扫描可信度提升

- 加入 Semgrep 结果复核
- 增加更稳定的规则归一化
- 对高危问题加二次确认链

### 阶段三：GUI 重构

- 拆分视图、线程、图表逻辑
- 减少单文件复杂度
- 降低 PyQt 图表依赖耦合
