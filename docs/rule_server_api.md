# 代码漏洞扫描器规则服务器API文档

本文档详细描述了代码漏洞扫描器规则服务器应提供的API接口规范，以便客户端可以获取、提交和管理漏洞检测规则。

## 基本信息

- **基础URL**: `https://your-rule-server.com/api`
- **认证方式**: API密钥（在HTTP头部使用`X-API-Key`字段）
- **数据格式**: 所有请求和响应均使用JSON格式

## API概览

| 端点 | 方法 | 描述 |
|------|------|------|
| `/rules` | GET | 获取所有规则列表 |
| `/rules/{rule_id}` | GET | 获取特定规则详情 |
| `/rules/search` | GET | 搜索规则 |
| `/rules/categories` | GET | 获取所有规则分类 |
| `/rules/languages` | GET | 获取支持的编程语言列表 |
| `/rules` | POST | 提交新规则 |
| `/rules/{rule_id}` | PUT | 更新现有规则 |
| `/rules/{rule_id}` | DELETE | 删除规则 |
| `/sync` | GET | 获取自某个时间点后更新的规则 |
| `/stats` | GET | 获取规则服务器统计信息 |

## 详细API说明

### 获取所有规则

获取所有可用的规则列表。

**请求**:
```
GET /api/rules
```

**查询参数**:
- `page`: 页码（默认为1）
- `limit`: 每页规则数量（默认为50，最大100）
- `severity`: 按严重级别筛选（可选）
- `language`: 按编程语言筛选（可选）
- `category`: 按类别筛选（可选）

**响应**:
```json
{
  "status": "success",
  "total": 152,
  "page": 1,
  "limit": 50,
  "rules": [
    {
      "id": "SQL_INJECTION_001",
      "name": "SQL注入风险检测",
      "description": "检测可能导致SQL注入的代码模式",
      "severity": "high",
      "languages": ["python", "php", "java"],
      "category": "SQL注入",
      "created_at": "2023-05-15T10:30:00Z",
      "updated_at": "2023-06-20T14:45:30Z"
    },
    // ... 更多规则
  ]
}
```

### 获取特定规则详情

获取特定规则的完整详情。

**请求**:
```
GET /api/rules/{rule_id}
```

**响应**:
```json
{
  "status": "success",
  "rule": {
    "id": "SQL_INJECTION_001",
    "name": "SQL注入风险检测",
    "description": "检测可能导致SQL注入的代码模式",
    "severity": "high",
    "languages": ["python", "php", "java"],
    "category": "SQL注入",
    "patterns": [
      {
        "pattern": "/(execute|query)\\s*\\(\\s*['\\\"][^'\\\"]*\\s*\\+/",
        "description": "检测字符串拼接SQL"
      },
      {
        "pattern": "/(execute|query)\\s*\\(\\s*f['\\\"]/"
      }
    ],
    "negative_patterns": [
      {
        "pattern": "parameterized_query"
      }
    ],
    "message": "检测到潜在的SQL注入风险。请使用参数化查询替代字符串拼接。",
    "fix_suggestion": "# 不安全代码\ncursor.execute(\"SELECT * FROM users WHERE username = '\" + username + \"'\")\n\n# 安全代码\ncursor.execute(\"SELECT * FROM users WHERE username = %s\", (username,))",
    "references": [
      "https://owasp.org/www-community/attacks/SQL_Injection"
    ],
    "created_at": "2023-05-15T10:30:00Z",
    "updated_at": "2023-06-20T14:45:30Z",
    "created_by": "system",
    "version": 2
  }
}
```

### 搜索规则

按关键词搜索规则。

**请求**:
```
GET /api/rules/search?q={search_term}
```

**查询参数**:
- `q`: 搜索关键词（必填）
- `page`: 页码（默认为1）
- `limit`: 每页规则数量（默认为20）

**响应**:
```json
{
  "status": "success",
  "total": 5,
  "results": [
    {
      "id": "SQL_INJECTION_001",
      "name": "SQL注入风险检测",
      "description": "检测可能导致SQL注入的代码模式",
      "severity": "high",
      "category": "SQL注入"
    },
    // ... 更多结果
  ]
}
```

### 获取规则分类

获取所有可用的规则分类列表。

**请求**:
```
GET /api/rules/categories
```

**响应**:
```json
{
  "status": "success",
  "categories": [
    {
      "id": "sql-injection",
      "name": "SQL注入",
      "description": "SQL注入相关的漏洞检测规则",
      "rule_count": 15
    },
    {
      "id": "xss",
      "name": "跨站脚本攻击",
      "description": "XSS相关的漏洞检测规则",
      "rule_count": 12
    },
    // ... 更多分类
  ]
}
```

### 获取支持的编程语言

获取规则服务器支持的所有编程语言列表。

**请求**:
```
GET /api/rules/languages
```

**响应**:
```json
{
  "status": "success",
  "languages": [
    {
      "id": "python",
      "name": "Python",
      "rule_count": 45
    },
    {
      "id": "javascript",
      "name": "JavaScript",
      "rule_count": 38
    },
    // ... 更多语言
  ]
}
```

### 提交新规则

提交一个新的漏洞检测规则。

**请求**:
```
POST /api/rules
Content-Type: application/json
X-API-Key: your-api-key

{
  "id": "XSS_VULNERABLE_OUTPUT",
  "name": "XSS易受攻击的输出",
  "description": "检测直接将用户输入输出到HTML而没有适当转义的代码",
  "severity": "high",
  "languages": ["javascript", "php"],
  "category": "XSS",
  "patterns": [
    {
      "pattern": "/document\\.write\\([^)]*\\$\\{/",
      "description": "检测document.write中的模板字符串"
    },
    {
      "pattern": "/\\.innerHTML\\s*=\\s*[^;]*(?:\\$\\{|\\+)/",
      "description": "检测innerHTML中的字符串拼接或模板字符串"
    }
  ],
  "message": "检测到潜在的XSS漏洞。请确保在输出到HTML前对用户输入进行适当转义。",
  "fix_suggestion": "// 不安全代码\nelement.innerHTML = '欢迎, ' + userName;\n\n// 安全代码\nconst textNode = document.createTextNode('欢迎, ' + userName);\nelement.appendChild(textNode);",
  "references": [
    "https://owasp.org/www-community/attacks/xss/"
  ]
}
```

**响应**:
```json
{
  "status": "success",
  "message": "规则创建成功",
  "rule_id": "XSS_VULNERABLE_OUTPUT",
  "created_at": "2023-07-10T08:15:22Z"
}
```

### 更新现有规则

更新一个现有的规则。

**请求**:
```
PUT /api/rules/{rule_id}
Content-Type: application/json
X-API-Key: your-api-key

{
  "name": "更新后的规则名称",
  "description": "更新后的描述",
  "patterns": [
    // 更新后的模式
  ],
  // ... 其他更新字段
}
```

**响应**:
```json
{
  "status": "success",
  "message": "规则更新成功",
  "rule_id": "XSS_VULNERABLE_OUTPUT",
  "updated_at": "2023-07-11T09:20:45Z",
  "version": 2
}
```

### 删除规则

删除一个现有的规则。

**请求**:
```
DELETE /api/rules/{rule_id}
X-API-Key: your-api-key
```

**响应**:
```json
{
  "status": "success",
  "message": "规则删除成功",
  "rule_id": "XSS_VULNERABLE_OUTPUT"
}
```

### 同步规则

获取自某个时间点后更新的所有规则，用于客户端同步。

**请求**:
```
GET /api/sync?since=2023-06-01T00:00:00Z
```

**查询参数**:
- `since`: ISO 8601格式的时间戳（必填）

**响应**:
```json
{
  "status": "success",
  "updated_since": "2023-06-01T00:00:00Z",
  "total": 25,
  "rules": [
    // 完整的规则对象列表
  ],
  "deleted_rules": [
    "REMOVED_RULE_001",
    "REMOVED_RULE_002"
  ],
  "server_time": "2023-07-15T10:30:45Z"
}
```

### 获取服务器统计信息

获取规则服务器的统计信息。

**请求**:
```
GET /api/stats
```

**响应**:
```json
{
  "status": "success",
  "stats": {
    "total_rules": 256,
    "rules_by_severity": {
      "critical": 42,
      "high": 78,
      "medium": 95,
      "low": 35,
      "info": 6
    },
    "rules_by_language": {
      "python": 85,
      "javascript": 72,
      "java": 45,
      // ... 更多语言
    },
    "rules_by_category": {
      "sql-injection": 25,
      "xss": 18,
      // ... 更多分类
    },
    "last_updated": "2023-07-14T18:30:22Z",
    "server_version": "1.2.0"
  }
}
```

## 错误处理

当API请求出错时，服务器将返回适当的HTTP状态码和包含错误信息的JSON响应：

```json
{
  "status": "error",
  "error": {
    "code": "rule_not_found",
    "message": "未找到指定ID的规则",
    "details": "请求的规则ID 'NON_EXISTENT_RULE' 不存在"
  }
}
```

常见HTTP状态码：
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未提供API密钥或API密钥无效
- `403 Forbidden`: 无权执行请求的操作
- `404 Not Found`: 请求的资源不存在
- `429 Too Many Requests`: 请求频率超过限制
- `500 Internal Server Error`: 服务器内部错误

## 速率限制

为防止滥用，API实施了速率限制：
- 匿名请求: 60次/小时
- 认证请求: 1000次/小时

超出限制时，服务器将返回`429 Too Many Requests`状态码，并在响应头中包含以下信息：
- `X-RateLimit-Limit`: 允许的最大请求数
- `X-RateLimit-Remaining`: 当前周期内剩余的请求数
- `X-RateLimit-Reset`: 速率限制重置时间（Unix时间戳）

## 客户端集成示例

### Python客户端示例

```python
import requests
import time

class RuleServerClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers['X-API-Key'] = api_key
            
    def get_rules(self, page=1, limit=50, severity=None, language=None):
        params = {'page': page, 'limit': limit}
        if severity:
            params['severity'] = severity
        if language:
            params['language'] = language
            
        response = requests.get(f"{self.base_url}/rules", 
                               headers=self.headers,
                               params=params)
        response.raise_for_status()
        return response.json()
        
    def sync_rules(self, since_timestamp):
        params = {'since': since_timestamp}
        response = requests.get(f"{self.base_url}/sync",
                               headers=self.headers,
                               params=params)
        response.raise_for_status()
        return response.json()
```

### 定期同步示例

```python
import datetime
import json
import os

def sync_rules():
    client = RuleServerClient("https://rules.example.com/api", "your-api-key")
    
    # 读取上次同步时间
    last_sync_file = os.path.expanduser("~/.codescan/last_sync.json")
    if os.path.exists(last_sync_file):
        with open(last_sync_file, 'r') as f:
            data = json.load(f)
            last_sync = data.get('last_sync')
    else:
        # 如果是首次同步，获取所有规则
        last_sync = "1970-01-01T00:00:00Z"
    
    # 执行同步
    sync_result = client.sync_rules(last_sync)
    
    # 处理更新的规则
    for rule in sync_result['rules']:
        save_rule(rule)
    
    # 处理删除的规则
    for rule_id in sync_result['deleted_rules']:
        delete_rule(rule_id)
    
    # 更新同步时间
    with open(last_sync_file, 'w') as f:
        json.dump({'last_sync': sync_result['server_time']}, f)
    
    print(f"同步完成。更新了 {len(sync_result['rules'])} 条规则，删除了 {len(sync_result['deleted_rules'])} 条规则。")
```

## 部署规则服务器

如需部署自己的规则服务器，可参考以下步骤：

1. 克隆规则服务器仓库: `git clone https://github.com/example/rule-server.git`
2. 安装依赖: `pip install -r requirements.txt`
3. 配置数据库连接
4. 启动服务器: `python server.py`

完整的部署文档请参考[规则服务器部署指南](https://github.com/example/rule-server/docs/deployment.md)。 