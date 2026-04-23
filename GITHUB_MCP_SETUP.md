# GitHub MCP Server 安装说明

## 安装完成 ✅

GitHub MCP Server 已成功配置为远程服务器。

## 配置详情

- **服务器名称**: `github.com/github/github-mcp-server`
- **服务器类型**: HTTP 远程服务器
- **服务器 URL**: `https://api.githubcopilot.com/mcp/`
- **配置文件位置**: `~/.cline/data/cline_mcp_settings.json`

## 认证方式

当前配置使用 OAuth 认证（通过 GitHub Copilot）。首次使用时，系统会提示您进行 OAuth 授权。

## 可用功能

GitHub MCP Server 提供以下主要功能组：

### 1. 仓库管理 (repos)
- 浏览和查询代码
- 搜索文件
- 分析提交
- 理解项目结构

### 2. 问题管理 (issues)
- 创建、更新和管理 issues
- 查看 issue 评论
- 管理标签和里程碑

### 3. 拉取请求 (pull_requests)
- 创建和合并 PR
- 查看 PR 审查和评论
- 更新 PR 分支

### 4. GitHub Actions (actions)
- 监控工作流运行
- 查看构建日志
- 管理工作流和作业

### 5. 代码安全 (code_security)
- 查看代码扫描警报
- 分析 Dependabot 警报

### 6. 其他功能
- 用户和团队管理
- 通知管理
- Gist 管理
- 项目管理
- 讨论管理

## 默认工具集

默认启用的工具集包括：
- `context` - 提供当前用户和 GitHub 上下文信息
- `repos` - 仓库相关工具
- `issues` - Issues 相关工具
- `pull_requests` - 拉取请求相关工具
- `users` - 用户相关工具

## 使用示例

重启 Cline 后，您可以尝试以下命令：

### 获取用户信息
```
get_me
```

### 列出仓库的 issues
```
list_issues owner="github" repo="github-mcp-server"
```

### 搜索代码
```
search_code query="language:python repo:github/github-mcp-server"
```

### 创建 issue
```
issue_write owner="your-username" repo="your-repo" method="create" title="Issue 标题" body="Issue 描述"
```

## 注意事项

1. **首次使用**: 重启 Cline 后，首次使用 GitHub MCP 工具时会触发 OAuth 认证流程
2. **权限范围**: 服务器会根据使用的工具请求相应的 GitHub 权限
3. **远程服务器**: 当前使用的是 GitHub 托管的远程服务器，无需本地安装 Docker 或 Go
4. **网络要求**: 需要能够访问 `api.githubcopilot.com`

## 故障排除

如果遇到问题：

1. **认证失败**: 确保 GitHub Copilot 已正确配置
2. **网络错误**: 检查网络连接和防火墙设置
3. **权限错误**: 确认您的 GitHub 账号有访问目标仓库的权限

## 更多信息

- GitHub MCP Server 仓库: https://github.com/github/github-mcp-server
- 完整文档: https://github.com/github/github-mcp-server/blob/main/README.md