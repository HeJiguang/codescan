# 贡献指南

感谢您对代码漏洞风险检查软件的关注！我们欢迎各种形式的贡献，包括但不限于：

- 代码贡献
- 文档改进
- 问题报告
- 功能建议
- 规则开发

## 开发环境设置

1. 克隆项目仓库
   ```bash
   git clone https://github.com/HeJiguang/codescan.git
   cd codescan
   ```

2. 创建虚拟环境
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate  # Windows
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # 开发依赖
   ```

4. 设置API密钥（用于测试）
   ```bash
   python -m codescan config --api-key YOUR_TEST_API_KEY
   ```

## 代码风格

我们使用以下代码风格指南：

- PEP 8 Python代码风格
- 函数和类应该有文档字符串
- 保持代码简洁清晰
- 使用类型注解提高代码可读性

我们使用以下工具进行代码质量检查：

- pylint
- flake8
- mypy (类型检查)

在提交代码前请运行：
```bash
python -m pytest
pylint codescan
flake8 codescan
mypy codescan
```

## 提交Pull Request

1. 创建一个分支用于你的开发工作
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. 进行代码更改和测试

3. 提交更改，使用清晰的提交信息
   ```bash
   git commit -m "Add feature: your feature description"
   ```

4. 推送到你的分支
   ```bash
   git push origin feature/your-feature-name
   ```

5. 创建Pull Request

## 开发新功能

如果你想开发新功能，请先创建一个Issue讨论你的想法，确保它符合项目方向并避免重复工作。

开发新功能时请注意：

1. 添加必要的测试
2. 更新相关文档
3. 遵循现有的代码架构和模式

## 开发新规则

如果你想贡献新的漏洞检测规则：

1. 查看[规则编写指南](../rules_guide.md)
2. 测试你的规则在不同类型的代码上的表现
3. 提交规则文件和测试用例

## 报告问题

报告问题时请包含以下信息：

1. 问题的详细描述
2. 重现问题的步骤
3. 预期行为和实际行为
4. 运行环境（操作系统、Python版本等）
5. 可能的截图或日志

## 提问和讨论

如有任何问题或讨论，可以：

1. 在GitHub Issues中提问
2. 发送邮件至sinwtao@outlook.com
3. 加入我们的开发者社区讨论

## 代码审查

所有提交的代码都将经过审查。审查关注点包括：

1. 代码质量和可读性
2. 测试覆盖率
3. 文档完整性
4. 安全性考虑
5. 性能影响

## 发布流程

我们使用语义化版本控制：

- 主版本号：不兼容的API变更
- 次版本号：向后兼容的功能性新增
- 修订号：向后兼容的问题修正

每个版本发布前会进行全面测试，确保软件质量。

## 行为准则

请参考我们的[行为准则](CODE_OF_CONDUCT.md)，保持尊重和专业的交流环境。

## 许可证

通过贡献代码，您同意您的贡献将基于MIT许可证进行许可。 