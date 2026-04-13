# Forms 答卷 MCP（`tools/forms-mcp`）

在 **Cursor**（或其他 MCP 客户端）中通过 **Microsoft Forms API** 读取并总结 **已提交的答卷**。数据来源是 **Forms 服务**，不是 Teams 频道里的帖子文本。

## 何时阅读本页

- 你持有表单的 `forms.office.com`（或同类）链接，希望在编辑器里获得 **答卷摘要**、按题汇总等。
- 你需要 **表单后台的提交记录**，而不是“谁在频道里贴了链接”。

## 安装与配置

完整步骤见仓库内说明（虚拟环境、Cursor MCP、`summarize_form_responses`、登录与权限等）：

- 在 GitHub 浏览：[tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md)
- 克隆本仓库后的本地路径：`tools/forms-mcp/README.md`

## 与「Teams 频道中的 Forms 链接」对照

| | **Forms 答卷 MCP**（本页） | **[Teams 频道中的 Forms 链接](forms-mcp.md)** |
| --- | --- | --- |
| 数据来自 | Forms API（提交记录） | Teams 频道消息（含链接的帖子与回复） |
| 典型入口 | `tools/forms-mcp/server.py` | `tools/teams` 扫描、`tools/teams-mcp` |
| 典型用途 | 总结、分析真实答卷 | 导出含 Forms URL 的频道帖子 JSON |

## 相关页面

- [Teams 频道中的 Forms 链接](forms-mcp.md)
- [Teams MCP](teams-mcp.md)
