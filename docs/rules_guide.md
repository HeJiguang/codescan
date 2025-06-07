# 规则编写指南

本指南介绍如何为代码漏洞风险检查软件创建自定义规则。系统支持多种规则格式，可以根据需要选择最适合的方式。

## 规则类型

系统支持以下几种类型的规则：

1. **基本规则**：使用JSON格式定义的简单规则
2. **正则表达式规则**：使用正则表达式匹配代码模式
3. **语义规则**：基于代码语义的复杂规则
4. **Semgrep规则**：兼容Semgrep格式的规则

## 基本规则结构

基本规则使用JSON格式定义，结构如下：

```json
{
  "id": "unique-rule-id",
  "name": "规则名称",
  "description": "详细描述",
  "language": "适用的编程语言",
  "severity": "严重程度",
  "pattern": "匹配模式",
  "message": "漏洞提示信息",
  "cwe": "CWE编号",
  "owasp": "OWASP分类",
  "remediation": "修复建议"
}
```

### 字段说明

- **id**：规则的唯一标识符，建议使用有意义的名称，如`sql-injection-001`
- **name**：规则的人类可读名称
- **description**：详细描述规则检测的安全问题
- **language**：适用的编程语言，可以是具体语言如`python`、`java`，也可以是`common`表示适用于所有语言
- **severity**：严重程度，可选值包括：
  - `critical`：严重，可能导致系统完全被控制
  - `high`：高危，可能导致敏感信息泄露或局部控制
  - `medium`：中危，可能导致服务中断或功能受损
  - `low`：低危，影响有限，但仍需注意
  - `info`：提示，不直接构成安全威胁，但可能有改进空间
- **pattern**：匹配模式，可以是字符串或正则表达式
- **message**：发现漏洞时显示的提示信息
- **cwe**：相关的CWE（Common Weakness Enumeration）编号，如`CWE-89`
- **owasp**：相关的OWASP分类，如`A1:2021-Injection`
- **remediation**：如何修复该安全问题的建议

## 正则表达式规则

正则表达式规则使用正则表达式模式匹配代码中的漏洞模式。示例：

```json
{
  "id": "hard-coded-password",
  "name": "硬编码密码检测",
  "description": "检测代码中的硬编码密码",
  "language": "common",
  "severity": "high",
  "regex": "(?i)(password|passwd|pwd)\\s*=\\s*['\"][^'\"]+['\"]",
  "message": "发现硬编码密码，建议使用配置文件或环境变量存储敏感信息",
  "cwe": "CWE-798",
  "owasp": "A07:2021-Identification and Authentication Failures",
  "remediation": "使用配置文件、环境变量或安全的密钥管理服务存储密码"
}
```

### 正则表达式技巧

- 使用`(?i)`进行不区分大小写的匹配
- 使用`\\b`匹配单词边界
- 使用`\\s*`匹配任意空白字符
- 使用捕获组`()`捕获特定部分
- 记得转义特殊字符，如`\`, `.`, `*`, `+`, `?`, `^`, `$`, `(`, `)`, `[`, `]`, `{`, `}`, `|`

## 语义规则

语义规则使用更复杂的模式，考虑代码的语义和上下文。这类规则需要提供更多信息：

```json
{
  "id": "insecure-deserialization",
  "name": "不安全的反序列化",
  "description": "检测使用pickle等不安全的反序列化库处理不可信数据",
  "language": "python",
  "severity": "critical",
  "semantic": {
    "imports": ["pickle", "cPickle"],
    "functions": ["loads", "load"],
    "contexts": ["request", "user_input", "file.read"]
  },
  "message": "使用pickle处理不可信数据可能导致远程代码执行",
  "cwe": "CWE-502",
  "owasp": "A08:2021-Software and Data Integrity Failures",
  "remediation": "对于不可信数据，使用JSON等安全的序列化格式，或在安全沙箱中执行反序列化"
}
```

## Semgrep规则

系统支持导入和使用Semgrep规则。Semgrep是一个强大的代码静态分析工具，使用类似于代码的模式匹配语法。

示例Semgrep规则（YAML格式）：

```yaml
rules:
  - id: insecure-jwt-none-algorithm
    pattern: |
      jwt.decode($TOKEN, ...)
    pattern-not: |
      jwt.decode($TOKEN, ..., algorithms=[...])
    message: JWT token decoded without specifying algorithms
    languages: [python]
    severity: ERROR
    metadata:
      cwe: CWE-347
      owasp: A2:2017-Broken Authentication
```

要使用Semgrep规则，可以从Semgrep规则库导入或自己编写。

## 规则存放位置

自定义规则应存放在以下位置：

- 系统级规则：`~/.codescan/rules/`
- 项目级规则：`<project_root>/.codescan/rules/`

规则文件可以按照以下方式组织：

```
rules/
├── common/          # 通用规则
│   ├── security.json
│   └── best_practices.json
├── python/          # Python特定规则
│   ├── django.json
│   └── flask.json
├── java/            # Java特定规则
│   ├── spring.json
│   └── android.json
└── semgrep/         # Semgrep规则
    ├── python/
    └── java/
```

## 规则测试

创建规则后，建议进行测试以确保规则能够正确检测漏洞。可以创建包含已知漏洞的测试代码，然后使用以下命令测试规则：

```bash
python -m codescan file path/to/test_file.py --rule-test
```

测试报告将显示哪些规则被触发，以及匹配的代码位置。

## 规则优先级

当多个规则匹配同一代码段时，系统会根据以下优先级决定使用哪个规则：

1. 特定语言的规则优先于通用规则
2. 自定义规则优先于内置规则
3. 项目级规则优先于系统级规则
4. 严重程度高的规则优先于严重程度低的规则

## 最佳实践

### 编写有效规则的建议

1. **保持规则简单**：规则越简单，误报率越低
2. **提供详细信息**：包括清晰的描述、CWE编号和修复建议
3. **考虑上下文**：尽量考虑代码的上下文，避免误报
4. **使用精确的模式**：正则表达式应该尽可能精确
5. **测试多种情况**：测试不同的代码样例，包括应该匹配和不应该匹配的案例
6. **更新和维护**：随着新漏洞的发现，定期更新规则

### 常见漏洞类型

以下是一些常见的漏洞类型，可以作为编写规则的参考：

1. **注入类**：SQL注入、命令注入、LDAP注入等
2. **认证和会话管理**：不安全的认证、会话固定等
3. **敏感数据泄露**：硬编码密钥、不安全的数据存储等
4. **XXE和SSRF**：XML外部实体、服务器端请求伪造
5. **访问控制**：越权访问、不安全的直接对象引用等
6. **安全配置错误**：默认配置、开发模式等
7. **跨站脚本**：存储型XSS、反射型XSS等
8. **不安全的反序列化**：Pickle、YAML等
9. **使用有漏洞的组件**：过时的库、组件等
10. **不足的日志和监控**：缺少关键操作日志等

## 示例规则库

查看我们的[示例规则库](https://github.com/yourusername/code-vulnerability-scanner/tree/main/examples/rules)获取更多示例规则。

## 社区贡献

我们欢迎社区贡献规则。如果您开发了有用的规则，请考虑通过Pull Request与社区分享。请参考[贡献指南](docs/CONTRIBUTING.md)了解具体步骤。 