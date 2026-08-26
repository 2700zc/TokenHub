# 更新日志

## [0.0.2] - 2026-08-26

### 修复：用量数值不再显示（解析失败）

#### 问题原因
OpenCode.ai 的 `_server` 接口返回格式发生了变更：

- **旧格式**：`...usagePercent:0}`（整数百分比，百分比后直接结束）
- **新格式**：`...usagePercent:19.3,usage:231665560,limit:1200000000}`（浮点百分比，且新增 `usage`、`limit` 两个字段）

原有的正则表达式要求 `usagePercent` 后紧跟 `}`，且百分比只能匹配整数，导致新旧格式均无法匹配，三个用量周期全部显示 `--`。

#### 修改内容

| 文件 | 说明 |
| --- | --- |
| `src/api.py` | 更新 `parse_js_response` 正则，兼容新旧格式：百分比改为匹配浮点数 `[\d.]+`，不再要求 `}` 紧跟其后，忽略新增的 `usage`/`limit` 字段 |
| `src/logger.py` | 修复日志中百分比显示为 `N/A` 的问题（日志读取的字段名 `usagePercent` 与解析结果实际存储的 `percent` 不一致） |

#### 验证
- 本地直连接口实测：`rollingUsage 21.3% / weeklyUsage 32.3% / monthlyUsage 68.8%`，重置倒计时正常解析
- 重新打包后的 `dist/TokenHub.exe` 实测运行正常，悬浮窗正常显示数值

### 构建
- 重新打包产物：`dist/TokenHub.exe`（PyInstaller onefile，无控制台窗口）
- `dist/config.json` 已按最新 curl 配置恢复（Workspace ID / Cookie / Server ID）