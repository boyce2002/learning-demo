# SparkLab v0.2｜09 最终独立复核与提交建议

审查对象：本轮上传的 `SparkLab_v0.2(1).zip`  
结论：**可进入本地录屏与源码提交阶段（Conditional GO）**；不建议在尚无访客隔离的条件下开放公共可写服务。此次结论不等于视频/手机/屏幕阅读器验收已经完成。

## 一、独立复核证据

| 项目 | 本轮核验方式 | 结果 | 证据范围与限制 |
|---|---|---|---|
| 源码包完整性 | 解压并枚举 ZIP | 75 个归档条目，其中 63 个文件；约 1.3MB | 包含前后端源码、测试、README、00–08 文档、设计截图 |
| 清洁交付 | 文件名清单检查 | 通过 | 无 `.venv/`、`node_modules/`、`dist/`、SQLite 数据库、pytest 缓存、`.pyc`、日志；存在正常的 `backend/.env.example`，这不是密钥文件 |
| 后端自动化测试 | 独立执行 `python -m pytest -q` | **25 passed in 1.06s** | Python 3.13.5、pytest 9.0.2；与原报告的 Windows Python 环境不同 |
| 前端 TypeScript | 以此前上传的旧版本 ZIP 中的依赖快照，在新前端源码上执行 `tsc -b` | **通过（辅助性验证）** | 并非当前 Vite 6.4.5 的完整新版依赖集，不能作为最新版前端构建证明 |
| 最新版依赖安装/构建 | 尝试 `npm ci --offline`、联网 `npm ci` | **当前环境无法完成** | 离线缺少缓存；npm 仓库连接出现 `EAI_AGAIN`，所以未能独立复现新版 Vite 构建和 `npm audit` |
| 实际代码变更 | 与此前上传的 `SparkLab_v0.2.zip` 逐文件 SHA-256 比较（过滤依赖/临时产物） | **与报告基本一致** | 后端源码未变；更新 App、LearningJournal、ProgressPanel、API client、依赖和文档；新增 06–08 与 375px 截图 |
| 无障碍/竞态 | 对新前端源码做静态审查 | **主要机制实现到位** | 未在本环境独立运行 Chrome 浏览器交互；浏览器测试以提交者记录为参考 |
| 正式提交材料 | 检查 README 和 demo-script | **方案齐全，视频仍未完成** | 交付前需要真人录屏及最终压缩包复查 |

## 二、关键代码审查

### 1. 前端 P1 精修：主要风险已处理

- `frontend/src/App.tsx`：`closeJournal()` 中止旧请求并增加序号，使历史异步请求无法在关闭后覆盖新 UI；`openJournal()` 通过 `AbortController` 和请求 ID 双重保护；日期切换、reset、组件卸载包含取消路径。
- `frontend/src/components/LearningJournal.tsx`：对话框初次打开时将焦点移到关闭按钮；使用 `Tab` 和 `Shift+Tab` 约束焦点，`Escape` 关闭；useEffect 卸载时移除键盘监听并在触发按钮仍连接 DOM 时归还焦点。
- `frontend/src/components/ProgressPanel.tsx` 与 `frontend/src/api/client.ts`：将触发按钮 ref 和历史请求的 `AbortSignal` 衔接到业务流程。
- 没有发现需要阻止本地录屏提交的新增严重逻辑错误。对话框的背景滚动、真实触屏与屏幕阅读器仍属于人工复核范围。

### 2. 业务规则保持不变

新版本 `backend/app/services.py`、`routes.py` 等核心后端文件与此前版本一致。现有后端测试检查首次猜想锁定、completion 幂等、streak、history 参考日隔离、并发与安全开关，结果全部通过。

### 3. 保留的交付风险

- `demo_student` 为固定共享用户：正常模式也没有访客隔离，因此**不宜直接公开可写部署**。
- `.gitignore` 会忽略项目根目录的 `sparklab-*.png`；若采用 README 中的 `git archive` 打包流程，根目录旧截图将不会包含在正式源码包里。`docs/sparklab-final-journal-375.png` 有显式保留规则；需确认正式提交是否需要其他四张截图。
- `backend/app/database.py` 使用 `with sqlite3.Connection` 管理事务，但没有确保连接按预期显式关闭；属于 P2 资源管理优化，不必在三天 Demo 的最后阶段扩大重构范围。
- `index.html` 未提供 favicon，可产生无害 404；不影响核心演示，但可选地完善品牌图标。

## 三、最终放行标准

**当前状态：Conditional GO（本地演示和录屏）**。以下事项完成后，方可把任务视为真正“已提交”：

1. 按 `docs/demo-script.md` 录制 60–90 秒成片；镜头证明从错误猜想、解释、反思、完成、刷新恢复，到三天 streak、断学归零、手记回看。
2. 至少一台真实手机检查页面布局、软键盘、触屏滚动及手记对话框；桌面浏览器实际执行一遍从开始到关闭手记的 Tab/Shift+Tab/Escape。
3. 有条件时使用 NVDA 或 VoiceOver 核对手记标题、关闭按钮以及反馈信息的朗读。
4. 在原生 Windows 开发环境做最后一次 `npm.cmd ci && npm.cmd run build` 和 `npm.cmd audit`，保留完整成功日志；本轮独立环境因 npm 网络连接问题无法对最新版构建作出验证。
5. 初始化 Git 并核对 `git status --short`；先 `git commit`，再 `git archive` 输出到项目目录外；列出 ZIP 内容，确认保留完整源码、锁文件、测试、docs、README 且没有运行数据。
6. 正式投递的材料至少包含**可用的视频文件或 Demo 链接（二选一）**以及**简短设计说明**。若提供源码 ZIP，可作为附加材料，不能以源码 ZIP 取代任务要求的视频或链接。

## 四、建议的最终交付组合

- 必交：60–90 秒演示视频（例如 `SparkLab_Demo_90s.mp4`）。
- 必交：简短说明文档（从 `docs/design-rationale.md` 精简，重点：为什么先猜想、如何进行诚实反馈、如何把反思与星轨形成可回看积累、采用了什么技术和验证）。
- 附加：干净的源码 ZIP（例如 `SparkLab_v0.2_source.zip`）及 README。

**不要再扩展新功能。** 现阶段投入产出比最高的动作是完成真人交互验证、录屏、归档和提交。

---

*审查说明：本报告区分“在独立环境实际执行的验证”“源码静态审查”和“开发者报告中的浏览器结果”；没有将后两者冒充为独立浏览器验收。*
