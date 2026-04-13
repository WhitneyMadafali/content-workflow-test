# Forms 答卷 MCP（`tools/forms-mcp`）

在 **Cursor**（或其他 MCP 客户端）中通过 **Microsoft Forms API** 读取并总结 **已提交的答卷**。数据来源是 **Forms 服务**，不是 Teams 频道里的帖子文本。

## 何时阅读本页

- 你持有表单的 `forms.office.com`（或同类）链接，希望在编辑器里获得 **答卷摘要**、按题汇总等。
- 你需要 **表单后台的提交记录**，而不是“谁在频道里贴了链接”。

## 分步操作

下面假设你已 **克隆本仓库**，且本机有 **Python 3**。命令中的路径请换成你机器上的 **绝对路径**。

### A. 已有表单链接：在 Cursor 里用 MCP 总结（最常用）

**1) 安装 Forms MCP 依赖（每台机器一次）**

在仓库根目录执行：

```bash
cd tools/forms-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

记下本机 `tools/forms-mcp` 的完整路径，下一步要填进 Cursor。

**2) 在 Cursor 里注册 MCP（每台机器一次）**

打开 **Cursor → Settings → MCP**，新增一个服务器：

- **Command（命令）**：指向上一步的 `.venv/bin/python`（完整路径）。
- **Args（参数）**：`server.py` 的完整路径（与 `server.py` 同目录下的那个文件）。
- **环境变量**：设置 `BROWSER`，例如 `google-chrome`，以便设备码登录能打开浏览器。

配置保存后，如有需要请 **重启 Cursor** 或重新加载 MCP。JSON 示例（路径改成你的）：

```json
{
  "mcpServers": {
    "forms-responses": {
      "command": "/你的路径/content-workflow/tools/forms-mcp/.venv/bin/python",
      "args": ["/你的路径/content-workflow/tools/forms-mcp/server.py"],
      "env": {
        "BROWSER": "google-chrome"
      }
    }
  }
}
```

**3) 登录 Microsoft Forms（每台机器通常一次）**

终端执行（路径与浏览器按你的环境修改）：

```bash
cd /你的路径/content-workflow/tools/forms-mcp
BROWSER=google-chrome .venv/bin/python server.py auth-test
```

在浏览器中完成登录。成功后会在该目录下生成 **`.forms_token_cache.json`**（此文件 **不在 Git 中**，勿提交）。之后调用会复用该缓存，直至过期或你删除它。

**4) 在 Cursor 对话里要摘要**

1. 确认 MCP 服务已启用（若界面有开关）。
2. 在聊天中请助手调用 **`summarize_form_responses`**，并提供：
   - **`form_url`**：你的表单链接，例如 `https://forms.office.com/r/...`；若已知 **`form_id`** 也可使用。
3. 说明你需要 **简短文字总结**（而非原始 JSON）。仓库内 Cursor 规则会引导助手优先输出 **`executive_summary`** 类叙述。

**5) 若登录或 API 失败**

- 向 IT 确认租户是否允许使用 **Microsoft Forms** 委派权限；必要时在环境中设置 **`FORMS_CLIENT_ID`** 指向已在 Entra 中注册且具备 Forms 权限的应用。详见 [tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md) 中的 **Required permissions** 与排错表。

### B. 不用 Cursor：命令行快速验证

安装与 **§A** 相同。在 `tools/forms-mcp` 下执行（将 URL 换成你的表单）：

```bash
BROWSER=google-chrome .venv/bin/python server.py summarize-test --brief --form-url "https://forms.office.com/r/..." --top 25
```

`--brief` 会先输出 **`executive_summary`**，再输出各题的简短主题行；去掉 `--brief` 可得到含 **`respondent_texts`** 等的完整 JSON。

### C. 可选：表单链接只出现在 Teams 频道

需要 **第二套** 环境：`tools/teams` 的 venv 与 **Microsoft Graph** 登录（与 Forms 的 token **分开**）。简要流程：

1. 用 `tools/teams` 扫描频道并导出含 Forms 链接的 JSON（参见 [Teams 频道中的 Forms 链接](forms-mcp.md)）。
2. 在 `tools/forms-mcp` 下运行 `summarize_from_teams_export.py` 指向该 JSON，或使用一键脚本 `scan_channel_forms_summary.sh`。

命令细节、一键脚本与 **`--pick N`** 多表单选择见 [tools/forms-mcp/README.md](https://github.com/ovesorg/content-workflow/blob/master/tools/forms-mcp/README.md) 中的 **Teams channel → Forms summary**。

## 安装与配置（延伸阅读）

更完整的说明（权限、暴露的工具列表、常见问题）：

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
