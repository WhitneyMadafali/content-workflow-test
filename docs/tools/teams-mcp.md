# Teams MCP 使用指南

本页面说明如何使用 `tools/teams-mcp` 提供的 MCP 服务，访问 Teams 频道与聊天消息。

## 1) 从零开始（本地没有仓库）

### 前置条件

- 已安装 `git`
- 已安装 `python3` 与 `pip`
- 可使用 Microsoft 365 账号登录 Teams

### 克隆仓库

```bash
git clone https://github.com/ovesorg/content-workflow.git
cd content-workflow
```

## 2) 安装

```bash
cd tools/teams-mcp
pip install -r requirements.txt
```

## 2) 启动 MCP 服务

```bash
BROWSER=google-chrome python server.py
```

首次运行会触发 Microsoft 登录授权。

## 3) 在 MCP 客户端中接入

将 MCP server 命令配置为：

```bash
python tools/teams-mcp/server.py
```

如需固定浏览器（推荐 Chrome）：

```bash
BROWSER=google-chrome python tools/teams-mcp/server.py
```

## 4) 可用 MCP 工具

- `list_joined_teams`：列出当前用户可访问的 Teams
- `list_team_channels`：列出指定 Team 的频道
- `list_channel_messages`：读取频道消息（可包含回复）
- `list_chats`：列出个人/群组/会议聊天
- `list_chat_messages`：读取指定聊天会话消息
- `search_chat_messages`：跨聊天按关键词搜索消息

## 5) 常见使用场景

- 按团队和频道定位消息
- 检索包含指定关键词的聊天记录
- 为外部系统提供结构化消息输入（JSON）
