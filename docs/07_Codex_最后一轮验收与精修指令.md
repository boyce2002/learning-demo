# 给 Codex 的最后一轮指令：SparkLab v0.2 收尾与无障碍精修

你正在已有的 SparkLab v0.2 工作区工作。**不要推倒重写，不引入新的题目/AI/登录或新业务模块。** 当前目标是完成提交质量的最后一轮小修复，保留已跑通的 P0/P1 闭环。请先阅读 `AGENTS.md`、`README.md`、`docs/06_独立验收报告与提交清单.md`。

## 阶段 0：先阅读真实源码并汇报

在改动前先列出实际存在的相关文件、关键函数/组件名、调用链、计划修改点：

- `frontend/src/App.tsx`：`openJournal()`、`loadDashboard()`、日期切换、关闭弹窗与 showJournal 状态。
- `frontend/src/components/LearningJournal.tsx`：弹窗打开/关闭、`role="dialog"`、Tab/Shift+Tab、Escape、焦点归还。
- `frontend/src/api/client.ts`：`fetchHistory()` 是否支持 `AbortSignal`。
- `frontend/src/components/ProgressPanel.tsx`：打开手记的触发按钮。
- `frontend/src/styles/tokens.css`、`frontend/src/styles/global.css`：可见焦点和减少动效。
- `backend/app/database.py`：连接生命周期；若认为风险低，可记录建议而暂不修改。

**必须先输出“已存在文件 + 关键函数 + 为什么修改 + 不修改哪些逻辑”，再实际开发。**

## 阶段 1：修复星光手记的可访问性（P1）

实现以下可验证行为：

1. 点击“查看我的星光手记”，焦点进入对话框中的第一个可操作元素（建议关闭按钮）；对话框有可读标签。
2. Tab/Shift+Tab 在对话框可聚焦元素中循环，不能跳到背景主页面。
3. Escape 能关闭对话框；点击遮罩或现有关闭按钮仍能关闭。
4. 关闭后焦点返回触发按钮；若触发按钮已经卸载，要安全退化，不抛异常。
5. 页面缩放和移动端不改变现有样式；保留 `prefers-reduced-motion` 和焦点可见样式。
6. 避免重复添加全局监听器：监听随弹窗挂载/卸载清理。

禁止引入庞大的新 UI 框架。优先现有 React hooks、ref、keydown handler，或如需依赖，先解释理由。

## 阶段 2：修复历史请求竞态（P1）

1. 为 `fetchHistory()` 提供可选 `AbortSignal`，不要破坏现有调用。
2. 关闭手记、切换演示日期、组件卸载时取消旧 history 请求，并通过序号保护防止旧结果覆盖当前结果。
3. 重复快速点击打开/关闭/切换日期不会在错误提示里误报 `AbortError`。
4. 新打开的手记只能展示当前参考日期允许的历史；不能借由前端竞态“穿越”未来记录。
5. 保持后端 API 契约完全不变。

## 阶段 3：独立验收与交付清理（P0）

- 后端运行 `python -m pytest -q`，必须不低于现有 25 passed。
- 前端运行 `npm.cmd ci`（Windows PowerShell）和 `npm.cmd run build`，真正执行，不能只复述之前的日志。
- 手工/浏览器自动化检查：从错误猜想完成、刷新恢复、三天 streak、缺一天 streak 重置、手记倒序、移动端 375px、Esc、Tab/Shift+Tab、断网恢复。明确分开“已实测”和“仍待人工验证”。
- 清理最终交付：不要带 `.venv`、`node_modules`、`frontend/dist`、`backend/.pytest-tmp`、`*.sqlite3`、`.env` 等；保留依赖声明和必要截图。
- 公共访问前仍须评估固定 `demo_student` 共享数据。**不要把一个共享 reset API 当成安全公开演示方案。**
- 更新 `README.md` 和 `docs/demo-script.md`，确保演示日期仍位于后端 ±30 天窗口。

## 最终必须汇报

按 `改了什么 / 为什么 / 实际效果 / 验证记录 / 未验证项 / 交付材料` 六段报告；列出**真实修改过的文件与关键函数**，贴出完整测试命令和实际结果。不要把用户之前的验证结果写成这轮的新执行结果，不要声称创建了未实际产生的录屏或 URL。
