# Teams 扫描流程

本指南用于说明如何使用 `tools/teams` 工具扫描 Teams 组织结构、频道消息与回复，并导出 JSON。

## 1) 安装

```bash
cd tools/teams
pip install -r requirements.txt
```

## 2) 列出可访问 Teams

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --list-teams
```

## 3) 仅扫描 Teams 与频道结构

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py -o analyses/teams-structure.json
```

## 4) 扫描频道消息与回复

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --message-limit 50 --reply-limit 50 -o analyses/teams-messages.json
```

## 5) 跳过回复线程

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --skip-channel-replies -o analyses/teams-no-replies.json
```

## 6) 下载频道文件并写入 JSON

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --include-channel-messages --download-channel-files --max-channel-files 25 -o analyses/teams-full-scan.json
```

## 7) 用户操作建议

- 首次运行会触发 Microsoft 登录授权，建议使用 Chrome。
- 先跑 `--list-teams` 和小 `--message-limit` 验证权限。
- 再逐步增加消息量和文件下载数量，降低失败重试成本。
- 产出 JSON 建议保存在 `tools/teams/analyses/`。

## 8) 定位特定团队/频道/聊天内容

### 按团队名称筛选

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "OVES 全体" -o analyses/team-filtered.json
```

### 按频道名称筛选（在指定团队内）

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "OVES 全体" --channel-name "General" -o analyses/channel-filtered.json
```

### 查找频道内包含指定关键词的聊天消息

```bash
BROWSER=google-chrome python scripts/scan-teams-graph.py --team-name "产品团队" --channel-name "General" --include-channel-messages --message-contains "invoice approval" -o analyses/message-search.json
```

### 匹配规则（大小写/空格/近似匹配）

- 名称和关键词匹配不区分大小写。
- 可容忍空格与标点差异（例如 `NewManagerAssimilation` 也可匹配 `New Manager Assimilation`）。
- 支持轻微拼写误差的近似匹配。
