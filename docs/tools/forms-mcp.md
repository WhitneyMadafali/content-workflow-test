# Teams 频道中的 Forms 链接（扫描与 Teams MCP）

!!! warning "此页不是读取表单答卷的 MCP"

    若要在 **Cursor** 中通过 **Forms API** 读取或总结 **真实提交记录**，请使用 **[Forms 答卷 MCP](forms-responses-mcp.md)**（仓库路径 `tools/forms-mcp`）。

    **本页**仅说明：当 **Microsoft Forms 链接或说明发布在 Teams 频道** 时，如何用 **Teams 扫描** 或 **Teams MCP** 导出或预览 **频道帖子**（含链接的文本）。**不会**从 Forms 后台拉取全部答卷明细；需要原始答卷数据时请使用 Forms 导出、Power Automate 或 Graph Forms API（依租户策略而定）。

## 1) 适用场景

- 在固定 Teams 频道发布表单链接、收集反馈说明或讨论
- 需要批量导出该频道内 **包含 Microsoft Forms 链接** 的帖子（可选包含回复线程）

## 2) 安装

与 [Teams 扫描](teams-scan.md) 相同，在 `tools/teams` 目录安装依赖（若系统 Python 限制全局 pip，请使用虚拟环境）：

```bash
cd tools/teams
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 3) 推荐：仅保留含 Forms 链接的频道帖子

使用 `scan-teams-graph.py` 的 `--forms-links-only`，仅保留正文中包含 `forms.office.com` 或 `forms.microsoft.com` 的父级消息（可与 `--message-contains` 组合，两者同时匹配）：

```bash
BROWSER=google-chrome .venv/bin/python scripts/scan-teams-graph.py \
  --team-name "你的团队名称" \
  --channel-name "你的频道名称" \
  --include-channel-messages \
  --forms-links-only \
  --message-limit 100 \
  --reply-limit 30 \
  -o analyses/channel-forms-posts.json
```

可先缩小范围验证权限与结果：

```bash
BROWSER=google-chrome .venv/bin/python scripts/scan-teams-graph.py \
  --team-name "你的团队名称" \
  --channel-name "你的频道名称" \
  --include-channel-messages \
  --forms-links-only \
  --message-limit 20 \
  --reply-limit 10 \
  -o analyses/channel-forms-posts-sample.json
```

## 4) 在 MCP 客户端中读取同一频道

1. 按 [Teams MCP](teams-mcp.md) 启动 `tools/teams-mcp` 并完成登录。
2. 使用 `list_joined_teams`、`list_team_channels` 取得 `team_id` 与 `channel_id`。
3. 调用 `list_channel_messages`，在返回的 `body_preview` 中筛选包含 `forms.office.com` 或 `forms.microsoft.com` 的条目（或与关键词搜索结合）。

## 5) 限制与预期

| 能力 | 说明 |
|------|------|
| 频道帖子与回复 | 可导出为 JSON（Teams 扫描）或由 MCP 返回预览文本 |
| Forms 答卷数据库 | **不在**本流程范围内；需使用 [Forms 答卷 MCP](forms-responses-mcp.md) 或导出 / Graph |

## 6) 相关页面

- [Forms 答卷 MCP](forms-responses-mcp.md)
- [Teams 扫描](teams-scan.md)
- [Teams MCP](teams-mcp.md)
