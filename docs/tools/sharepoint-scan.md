# SharePoint 扫描流程

本指南用于说明如何使用 `tools/sharepoint` 工具扫描 SharePoint 文件夹或文件，并将结果导出为 JSON。

## 1) 安装

```bash
cd tools/sharepoint
pip install -r requirements.txt
```

## 2) 基础扫描（文件夹）

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>"
```

## 3) 输出到 JSON

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" -o analyses/folder-scan.json
```

## 4) 递归扫描子目录

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" --recursive --max-depth 10 -o analyses/folder-tree.json
```

## 5) 文件内容分析（PPT/Excel）

### 分析单个文件链接

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-file-link>" --analyze-file -o analyses/file-analysis.json
```

### 从文件夹中筛选并下载分析

```bash
python scripts/scan-sharepoint-graph.py "https://<your-sharepoint-folder-link>" --filter "1,4,5" --download-analyze -o analyses/filtered-analysis.json
```

## 6) 常用辅助命令

### 查看可访问站点

```bash
python scripts/scan-sharepoint-graph.py --list-sites
```

### 清理会话缓存

```bash
python scripts/scan-sharepoint-graph.py --cleanup-session
```

## 7) 用户操作建议

- 首次运行会弹出 Microsoft 登录窗口，请完成授权。
- 建议先进行小范围扫描（不递归）验证权限和链接。
- 再开启递归和分析模式，避免一次性数据过大。
- 输出 JSON 建议统一存放在 `tools/sharepoint/analyses/` 目录。
