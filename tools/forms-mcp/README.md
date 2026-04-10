# Forms MCP（文档入口）

本目录仅作为 **Forms MCP** 在仓库中的命名入口；**没有**独立的 MCP 服务端代码。

- **说明文档（MkDocs）：** [`docs/tools/forms-mcp.md`](../../docs/tools/forms-mcp.md)  
  构建后站点导航为 **Forms MCP**。
- **实现方式：** 使用 [`tools/teams`](../teams/) 中的 `scan-teams-graph.py`，加 `--include-channel-messages` 与 `--forms-links-only`，导出频道内含 Microsoft Forms 链接的帖子。
- **与 Teams MCP 的关系：** 若需在 MCP 客户端中读取频道消息，仍使用 [`tools/teams-mcp`](../teams-mcp/)，再在结果中筛选 Forms URL；详见文档。

快速命令示例：

```bash
cd ../teams
BROWSER=google-chrome .venv/bin/python scripts/scan-teams-graph.py \
  --team-name "Your team" \
  --channel-name "Your channel" \
  --include-channel-messages \
  --forms-links-only \
  -o analyses/channel-forms-posts.json
```
