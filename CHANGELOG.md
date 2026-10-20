# 更新日志

## [0.1.2] - 2026-09-30

### 修复：月末最后一天 DeepSeek 数据不显示

#### 问题原因
`src/api.py` 的 `_deepseek_today_range()` 计算“明天”时使用 `start_dt.replace(day=start_dt.day + 1)`。
在每月最后一天（如 9 月 30 日），`day=31` 超出当月合法范围，`datetime.replace` 直接抛出
`ValueError: day 31 must be in range 1..30 for month 9 in year 2026`，导致 DeepSeek 余额和用量请求
在发出前即失败，悬浮窗 DeepSeek 各列全部显示 `--`。

#### 修改内容

| 文件 | 说明 |
| --- | --- |
| `src/api.py` | `_deepseek_today_range()` 改用 `start_dt + timedelta(days=1)` 计算次日零点，正确处理月末 / 年末 / 闰年跨日 |

#### 验证
- 本地复现：9/30 运行原逻辑抛出与 exe 日志一致的 `ValueError: day 31 must be in range 1..30 for month 9 in year 2026`
- 修复后直连接口实测：`today range` 正确为 9/30 00:00 ~ 10/1 00:00，余额 `23.93 CNY`、今日用量正常解析
- 边界验证：9/30、12/31、2/28 均正确跨到次日

### 构建
- 重新打包产物：`dist/TokenHub.exe`（PyInstaller onefile，无控制台窗口）

## [0.1.1] - 2026-09-08

### 优化：悬浮窗改为“纵向厂商块”布局

- `src/floating_window.py`：
  - 悬浮窗宽度固定（760px），不再随列数拉长溢出屏幕；多数据源时改为纵向堆叠，高度按数据源数量自动增减
  - 每个数据源一块，块头标注厂商全名：OpenCode Go（蓝）/ CommandCode（青）/ DeepSeek（金）
  - 数据值颜色与厂商色一致，便于区分；移除原 CommandCode 指标的 `CC ·` 文字前缀（块头已能标识）
  - 贴边自动隐藏 / 拖动 / 圆角毛玻璃效果全部适配动态高度
- 帮助文档、README 同步更新为新布局说明

## [0.1.0] - 2026-09-08

### 新增：CommandCode 用量支持

- `src/config.py`：新增 `commandcode_enabled` / `commandcode_cookie` 配置项（旧配置自动兼容）
- `src/api.py`：
  - 新增 `extract_commandcode_token()`：从整段 curl / Cookie / 裸 token 中提取 `__Secure-commandcode_prod_.session_token`
  - 新增 `fetch_commandcode()`：请求 `/internal/billing/credits` + `/internal/billing/subscriptions`，解析为 5小时（滚动）/ 每周 / 每月 三段用量及距离重置时间
  - 容错：`windowLimits.limited=false`（按量付费）或无该字段时显示 `--` / “按量付费无上限”，不影响其他数据源
- `src/settings_window.py`：新增「显示 CommandCode 用量」开关、Session Token 输入框、「从curl导入」自动提取；窗口改为可滚动（内容变多后仍可完整访问）
- `src/floating_window.py`：三数据源（OpenCode / CommandCode / DeepSeek）列独立开关；CommandCode 三列沿用「滚动用量/每周用量/每月用量」标题，副标题带 `CC ·` 前缀以便与 OpenCode 区分，百分比保留两位小数（如 `0.19%`）；任一数据源出错只置灰自身列，不影响其他列
- `src/logger.py`：新增 `log_commandcode()` 及 CommandCode 响应日志
- `src/help_window.py` / `README.md`：补充 CommandCode 获取与配置步骤

#### 验证
- 实测真实账号：5小时用量 `0.19%`、每周用量 `0.33%`、每月用量 `0.16%`，重置倒计时均正常
- GUI 冒烟：三数据源同显、单源错误隔离、设置窗口滚动均正常

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