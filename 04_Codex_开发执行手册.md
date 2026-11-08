# SparkLab｜Codex 分阶段实施手册 v0.2

> 请把本手册和 `00`～`03` 文档放在工作区供 Codex 阅读，并把 `AGENTS.md` 放到项目根目录。下面的每个阶段都可以分别复制给 Codex。**必须先看到源码文件及函数清单，再让它修改源码**；且每阶段的结论必须基于真正执行过的命令。

## 0. 给 Codex 的第一条总指令（直接复制）

```text
你是负责交付面试 Demo 的全栈工程师与注重细节的 UI 工程师。
项目是「微光实验室 SparkLab」：每天 5 分钟完成一道微挑战，经过猜想、揭晓、反思、完成，点亮星轨并持久化真实连续学习天数。

请以当前工作区中的以下文档作为唯一规格依据，v0.2 优先于 v0.1：
1. 00_使用说明与决策记录.md
2. 01_产品流程与逐屏交互.md
3. 02_星空微光设计系统与逐屏文案.md
4. 03_后端接口数据模型与测试验收.md
5. 04_Codex_开发执行手册.md
6. AGENTS.md

技术固定：React + TypeScript + Vite；Python + FastAPI + Pydantic + SQLite；API 为真实 HTTP，业务状态以后端为准。不要登录、LLM、排行榜、付费功能。

开工前：
A. 先检查真实工作区现有文件（若空目录就明确说是新项目）；绝不假设不存在的源码已经实现。
B. 首先输出“预计新建/修改文件路径、每个文件关键函数/类、模块职责、接口列表、需要运行的命令、主要风险”，然后继续执行，不需要等待我批准。
C. 先实现可真实运行的 P0 闭环，再实现视觉完善，之后按剩余时间实现 P1。
D. 在每一阶段结束给出：修改了什么（逐文件）、为什么这么设计、真实执行的命令及输出摘要、已通过/未通过/未运行的验证项、遗留问题。不能用模拟结果冒充测试通过。
E. 代码遵守 v0.2 接口：POST attempt 真正写 daily_attempts；POST complete 只收 reflection 并读取已有 attempt；唯一索引保证每天只完成一次；GET today 能在刷新后恢复 not_started/attempted/completed。
F. 如果文档间有冲突，依次使用：03 接口与数据契约 > 01 产品流程 > 02 视觉文案 > 00 范围。v0.1 仅供历史参考。

现在从 Step 0 开始，先列出文件和函数清单，再创建代码、运行与测试。请保证 Windows PowerShell 可以按 README 启动。
```

## 1. 源码结构（建议，Codex 应给出最终真实路径）

```text
sparklab/
├── AGENTS.md
├── README.md
├── .gitignore
├── docs/
│   ├── design-rationale.md
│   └── demo-script.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/
│   │   └── tasks.json
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app, lifespan, routers, CORS
│   │   ├── config.py          # settings, DEMO_MODE, database path
│   │   ├── schemas.py         # Pydantic request / response
│   │   ├── tasks.py           # load_tasks, get_task_for_date, public_task
│   │   ├── clock.py           # now_utc, resolve_reference_date
│   │   ├── database.py        # connect_db, init_db, transaction helpers
│   │   ├── services.py        # record_attempt, complete_day, get_today, get_progress
│   │   └── routes.py          # /api/health/today/progress/tasks/dev
│   └── tests/
│       ├── conftest.py
│       ├── test_api_flow.py
│       ├── test_streak.py
│       └── test_demo_security.py
└── frontend/
    ├── package.json
    ├── index.html
    ├── vite.config.ts
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx             # orchestration; request abort/stale guard
        ├── types.ts           # API DTO and UI discriminated state
        ├── api/client.ts      # typed fetch, error normalization
        ├── content/copy.ts    # all page copy strings
        ├── styles/tokens.css  # visual variables, typography, motion
        ├── styles/global.css  # layout, responsive
        ├── components/
        │   ├── AppShell.tsx
        │   ├── DailyHeader.tsx
        │   ├── ChallengeCard.tsx
        │   ├── GuessStep.tsx
        │   ├── RevealStep.tsx
        │   ├── ReflectionStep.tsx
        │   ├── CompletionStep.tsx
        │   ├── ProgressPanel.tsx
        │   ├── StarOrbit.tsx
        │   ├── DemoToolbar.tsx      # P1
        │   └── LearningJournal.tsx # P1
        └── assets/             # Optional own SVG marks only
```

不要求逐字照搬结构，但**每个核心行为都必须定位到真实函数**。如采用更少文件，要解释为什么不影响测试与可维护性。

### 要在 Step 0 列出的函数参考

| 函数/类 | 职责（要由 Codex 核实并实现） |
|---|---|
| `resolve_reference_date` | 根据 DEMO_MODE、demo_date 与北京时区确定查询日期 |
| `get_task_for_date` | 固定锚点按天数映射唯一题目 |
| `public_task` | 未揭晓时过滤正确答案/解释 |
| `record_attempt` | 单次猜想、选项校验、事务幂等 |
| `complete_day` | 读取猜想、校验反思、事务幂等完成 |
| `compute_streak` / `get_progress` | 今日/昨日锚点 streak、历史累计、七日周星轨 |
| `get_today` | 组装 not_started/attempted/completed 可恢复状态 |
| `apiRequest` / `fetchToday` | 请求、异常归一化与 TypeScript 契约 |
| `onReveal` | 提交 attempt，处理 loading/失败/恢复 |
| `onComplete` | 提交 reflection，成功才更新 UI |
| `StarOrbit` | 七日星轨及无障碍 label |
| `DemoToolbar` | 本地日期模拟，不在非 demo 模式暴露 |

## 2. Step 1｜先实现后端 + 测试

**发给 Codex：**

```text
执行 Step 1：基于 03_后端接口数据模型与测试验收.md，实现 FastAPI + SQLite + 7 条人工题目 seed。
开始修改前先列：本阶段要改的文件路径、关键函数和调用关系，并区分新建/现有文件。

必须实现：
- GET /api/health、GET /api/today、GET /api/progress
- POST /api/tasks/{task_key}/attempt（存 daily_attempts、返回揭晓）
- POST /api/tasks/{task_key}/complete（只收 reflection，先检查 attempt，存 daily_completions）
- 后端可恢复三个 phase；本日任务按北京时区和固定 anchor day 选取
- SQLite unique + transaction 幂等，重复点击不增 streak/不覆盖反思
- 数据库注入可隔离的测试环境，不损坏本机 demo 数据
- 生产 DEMO_MODE=false 时拒绝 demo_date；公开默认不可 reset
- 至少跑 T01–T16，若条件允许加并发和时区边界测试

请实际运行 requirements 安装、pytest、API smoke 测试；如果失败就修复并重跑，最后贴真实命令和通过情况。不要在后端未通过验收之前设计虚假的前端进度。
```

### 后端验收门槛

- [ ] `python -m pytest -q`（在 backend 环境中）真实执行；报告通过数量与失败。
- [ ] 用 `TestClient` 或 `curl` 跑过：初次 today → attempt → complete → progress → 刷新 today。
- [ ] SQLite 磁盘中可查到一次 attempt + 一次 completion；重复提交记录数仍为 1。
- [ ] 非 DEMO 模式 `?demo_date=` 返回 403。
- [ ] 正常用户完全不需要任何本地密码/Token 就能完成 Demo；这是固定演示用户、不是生产认证设计。

## 3. Step 2｜前端先闭环，再视觉精修

**发给 Codex：**

```text
执行 Step 2：以 01_产品流程与逐屏交互.md 和 02_星空微光设计系统与逐屏文案.md 为 UI/文案依据。
开始改代码前先列要修改/新建的文件、关键 React 函数组件、props/state、用到的 API。

请构建“深蓝紫夜空 + 月白主卡 + 金色七日星轨”的成熟教育科技页面：
1. S0 加载/失败、S1 今日挑战、S2 猜想、S3 揭晓、S4 微反思、S5 完成。
2. GET today + progress 初始化，刷新后恢复 phase；主卡随步骤切换，不需要硬加复杂路由。
3. attempt 与 complete 必须调用真实后端；完成成功才出现星星动画与更新数字。
4. 未猜想不能揭晓；揭晓后选项锁定；反思去首尾空格 6–120 Unicode 字符；错误保留输入、支持重试。
5. 7 日星轨准确映射 done/missed/today_pending/future；今日/连续/累计来自 API。
6. 使用完整中文文案字典，不用“Lorem ipsum”或“Coming soon”假内容。
7. 视觉 token 使用指定色值与布局；桌面 1440px 双栏、375px 单栏、320px 不溢出；按钮≥44px；键盘导航；reduced-motion。
8. 仅在后端返回 is_demo_mode=true 时允许出现 DemoToolbar（如 P1 实现）。

真实运行 npm install、npm run build；尽量启动前后端做本机端到端检查。每个阶段请报告改了哪些文件、为什么，以及真实运行结果；不准声称未测的内容已通过。
```

### 前端验收门槛

- [ ] S1 → S5 可操作；支持正确或错误选择。
- [ ] 接口失败不提前点亮；重新连接后可继续。
- [ ] `npm run build` 真实完成。
- [ ] 375px 可输入、点击、滚动，无横向溢出；桌面主卡与星轨卡有清楚的主次。
- [ ] `aria-label`、`label`、focus、状态文字与 reduced-motion 具备。

## 4. Step 3｜联调、回归、演示模式（先保 P0）

**发给 Codex：**

```text
执行 Step 3：请先真实检查已存在的源码与日志，列出计划要改的文件和关键函数，避免猜测实现状态。
首先修复所有 P0 接口与页面问题；然后在 P0 全通过的前提下追加本地演示模式（P1）：
- DEMO_MODE=true 时切换模拟日期（今天 / +1 / +2 / +4，可选日期输入）。
- DEMO_RESET_ENABLED=true 且本地受控环境时允许重置两表记录；生产默认禁用。
- 日期切换需要防止前一次慢响应覆盖当前日期内容（request cancellation / stale key guard）。
- 验证 3 天连续完成、第四天未完成保留、第五天断档归零且累计不变。
- 如有余力再做星光手记（history API + 只读 UI）；没有就明确放入未完成项，不显示无效入口。

实际运行后端 pytest、前端 build、浏览器手动检查（若环境支持）；必须给出：每条验收用例的实际状态、控制台/命令输出、已知风险、最终启动方式。不能编造已录制视频、部署地址或人工浏览器截图。
```

## 5. Step 4｜交付准备

**发给 Codex：**

```text
执行 Step 4：请再次输出真实的“源码文件与核心函数索引”，然后完成交付材料。
- README：Windows PowerShell + macOS/Linux 启动命令、默认本地访问地址、API 文档 URL、如何启用/关闭 Demo 模式、重置流程、固定演示用户与模拟数据标识。
- docs/design-rationale.md：一页以内，说明需求、主动学习闭环、星空视觉为什么克制、连学天数与持久化、技术实现、已验证/未验证的点。
- docs/demo-script.md：60–90 秒镜头脚本，演示从零到第一颗星、刷新仍保存、模拟 3 天增长、漏学归零。
- 提供将代码提交或部署的建议，不要虚构已经存在的公开链接或视频文件。
- 最后列出 P0/P1 完成情况；每个功能都附实际证据（请求/测试/截图仅限真实生成的）。

如果你无法直接浏览网页或录屏，请如实说明并保留可由我本机完成的演示步骤。不要因为无法部署而伪称已上线。
```

## 6. 本地命令参考（最终以真正生成的项目结构为准）

### Windows PowerShell

```powershell
# 终端 A：后端
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# 演示视频时才按需启用：
$env:DEMO_MODE = "true"
$env:DEMO_RESET_ENABLED = "true"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端 B：前端
cd frontend
npm install
npm run dev

# 后端测试（在 backend 文件夹、虚拟环境已激活）
python -m pytest -q

# 前端构建（在 frontend 文件夹）
npm run build
```

### macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
DEMO_MODE=true DEMO_RESET_ENABLED=true python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 新终端
cd frontend
npm install
npm run dev
```

如采用 Vite dev proxy，在 `frontend/vite.config.ts` 中将 `/api` 代理到 `http://127.0.0.1:8000`；本地前端通常 `http://localhost:5173`，FastAPI 文档通常 `http://127.0.0.1:8000/docs`。**这些是预期默认地址，不代表当前已经有服务启动。**

## 7. 一套能讲清项目的验收证据表

| 层级 | 必须证明 | 证据形式 |
|---|---|---|
| 业务 | 从猜想到完成的每个状态都可演示 | 浏览器实际操作 + 录屏 |
| 数据 | 一天一次、刷新不变、连学可计算 | API 响应 + SQLite 测试 |
| 工程 | 前后端分层且具有自动化测试 | 路径/函数索引 + 命令输出 |
| 体验 | 易读、移动端、错误保护、友好反馈 | 375px 检查 + 截图/录屏 |
| 诚实性 | 全部模拟能力标注清楚 | UI badge + README + 说明书 |

### Codex 每阶段必须使用的汇报模版

```markdown
### Step N 实施报告
**改了什么（逐文件）：**
- `路径` — 关键函数/组件 — 行为变化

**为什么这样实现：**
- 对应 v0.2 哪一条产品或技术要求

**运行与验证（真实）：**
- 命令：`...`
- 结果：通过 / 失败 / 未执行 + 核心输出摘要

**影响和不足：**
- 对用户体验/接口/测试的影响；遗留事项

**下一步：**
- 下阶段将改动的具体文件名与关键函数名
```
