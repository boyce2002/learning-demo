# 微光实验室 SparkLab

一个可真实运行的全栈面试 Demo：匿名访客每天完成一道微挑战，依次经历“猜想 → 揭晓 → 反思 → 完成”，由 FastAPI + SQLite 持久化首次猜想、反思、连续学习天数和七日星轨。

> 诚实性说明：7 道题为人工预置题库；演示日期与成长记录均为模拟数据，不代表真实学生学习分析。公网模式由后端签发 `HttpOnly + Secure + SameSite=Lax` 签名 Cookie，各匿名访客的 attempt、completion、进度、历史和重置均隔离；它仍不是账号系统，清除 Cookie 或会话过期会开始一份新体验。

## 技术与目录

- 前端：React 18、TypeScript、Vite
- 后端：Python 3.9+、FastAPI、Pydantic、SQLite
- 权威状态：`backend/data/sparklab.sqlite3`（首次启动自动创建，已被 `.gitignore` 排除）
- 测试：pytest 使用独立临时 SQLite，不会清空运行中的演示库

```text
backend/app/       FastAPI、业务服务、SQLite、题目映射
backend/data/      7 道固定顺序人工题目；本地数据库运行时生成
backend/tests/     业务、幂等、并发、时区、历史与公网隔离测试
frontend/src/      S0–S7 页面、API 客户端、视觉 token 与响应式样式
docs/              设计说明与 60–90 秒演示脚本
Dockerfile         单容器构建前端并由 FastAPI 同域托管
render.yaml        Render Web Service + /data 持久磁盘 Blueprint
scripts/           无头 Chrome 公网形态 E2E
```

## Windows PowerShell 启动

在项目根目录执行一次安装：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
Set-Location .\frontend
npm.cmd ci
Set-Location ..
```

`npm ci` 会严格按 `package-lock.json` 重建依赖，适合正式验收和录屏前准备；只有在主动升级依赖并准备更新锁文件时才使用 `npm install`。

### 安全默认启动（推荐先验收）

正常模式不会开放模拟日期或 reset。终端 A：

```powershell
Set-Location .\backend
$env:DEMO_MODE = "false"
$env:DEMO_RESET_ENABLED = "false"
$env:DATABASE_PATH = ".\data\sparklab.sqlite3"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

终端 B：

```powershell
Set-Location .\frontend
npm.cmd run dev -- --host 127.0.0.1
```

两个进程都保持在可见终端中，按 `Ctrl+C` 即可停止；没有额外的一键脚本在后台静默开放调试接口。

### 本机录屏 Demo 模式

只有面试录屏需要日期切换和重置时，才在终端 A 显式开启本机 Demo 模式；仍只绑定 `127.0.0.1`：

```powershell
Set-Location .\backend
$env:DEMO_MODE = "true"
$env:DEMO_RESET_ENABLED = "true"
$env:DATABASE_PATH = ".\data\sparklab.sqlite3"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

终端 B 启动前端：

```powershell
Set-Location .\frontend
npm.cmd run dev
```

访问：

- 网页：<http://127.0.0.1:5173>
- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/health>

使用 `npm.cmd` 是为了兼容禁止执行 `npm.ps1` 的 Windows PowerShell 策略。也可以激活虚拟环境后使用 `python`；以上命令不依赖激活脚本，复制即可运行。

### 正常模式

非演示生产环境关闭日期覆盖和两种 reset；此时后端不会注册 reset 路由，传 `demo_date` 会得到 403，而不是被静默忽略。

```powershell
$env:DEMO_MODE = "false"
$env:DEMO_RESET_ENABLED = "false"
```

不要把本地 `.env`、`.venv`、`node_modules` 或 `*.sqlite3` 提交到仓库。

## 公网 Demo：单域 Docker 部署

公网模式使用一个进程、一个域名：FastAPI 同时提供 Vite `dist` 与 `/api`，SQLite 只写入 `/data/sparklab.sqlite3`。浏览器不提交 `user_id`；后端只接受由 `SESSION_SECRET` 签名的随机匿名访客 Cookie。`/api/demo/reset` 只删除当前访客的数据，危险的 `/api/dev/reset` 与 Swagger/OpenAPI 在公网模式不注册。

必要环境变量见 `.env.example`。关键安全值：

```text
PUBLIC_DEMO_ENABLED=true
VISITOR_RESET_ENABLED=true
DEMO_MODE=true
DEMO_RESET_ENABLED=false
COOKIE_SECURE=true
SESSION_SECRET=<平台生成的至少 32 字符随机值>
DATABASE_PATH=/data/sparklab.sqlite3
FRONTEND_DIST_PATH=/app/frontend/dist
```

本机验证镜像：

```powershell
docker build --tag sparklab-demo:step6 .
docker run --rm -p 127.0.0.1:8000:8000 `
  -e SESSION_SECRET=replace-with-a-random-32-character-secret `
  -e COOKIE_SECURE=false `
  -v sparklab-local-demo:/data `
  sparklab-demo:step6
```

正式 HTTPS 推荐使用根目录 `render.yaml` 创建 Render Blueprint。该清单使用当前 `0.5c-512mb` Web Service、1 GB `/data` 持久磁盘和平台生成的 256-bit `SESSION_SECRET`。Render 持久磁盘属于付费资源；不要改成无磁盘免费实例，否则重启/重新部署会丢失 SQLite 数据。

1. 将清洁源码提交到私有或公开 Git 仓库；确认 `git status` 不含 `.env`、SQLite、`.venv`、`node_modules`、`dist`。
2. 在 Render Dashboard 选择 **New Blueprint**，连接仓库并读取根目录 `render.yaml`。
3. 核对磁盘挂载 `/data`、`DEMO_RESET_ENABLED=false`、自动生成的 `SESSION_SECRET` 后创建服务。
4. 只有当 `https://<service>.onrender.com/api/health` 为 200，且两个无痕窗口隔离、重启恢复均通过后，才把链接写入提交材料。

SQLite 持久磁盘只能挂在单实例服务上，不能横向扩容；当前内存限流器同样按单实例设计。这符合小流量面试 Demo，不适合作为多租户生产学习平台。

## macOS / Linux 启动

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# 终端 A
cd backend
DEMO_MODE=true DEMO_RESET_ENABLED=true DATABASE_PATH=./data/sparklab.sqlite3 \
  ../.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端 B（项目根目录起）
cd frontend
npm run dev
```

## 测试与构建

```powershell
# 项目根目录
Set-Location .\backend
..\.venv\Scripts\python.exe -m pytest -q

Set-Location ..\frontend
npm.cmd ci
npm.cmd exec tsc -- -b
npm.cmd run build
```

2026-11-07 Step 5 本轮实际回归结果：后端 `25 passed in 21.35s`；独立 TypeScript `tsc -b` 通过；Vite 6.4.5 production build 通过（42 modules transformed，968ms）；`npm ci` 安装 70 个包、审计 71 个包，显式 `npm audit` 为 0 vulnerabilities。生产安全模式的 `/api/health` 返回 200，SQLite 两张表成功初始化，`demo_date` 返回 403，reset 返回 404。系统 Chrome headless 使用真实 DemoToolbar 跑过错误猜想到完成、刷新恢复、连续三天与漏学重置、历史倒序/过去视角、手记焦点循环与 Escape、历史慢请求竞态、完成请求断网保留反思并重试；375px 根节点 `scrollWidth=375`。浏览器证据见 `docs/sparklab-final-journal-375.png`，完整人工检查表见 `docs/11_最终交付验收与人工检查清单.md`。

2026-11-08 Step 6 本轮最终结果：`33 passed in 31.59s`；`npm ci` 安装 70 包且 0 漏洞；独立 `tsc -b` 通过；Vite production build 42 modules、2.13s；`npm audit` 各级均为 0。Docker 镜像真实构建成功，容器写入后删除/重建容器并复用测试卷，完成状态和反思成功恢复。两个独立无头 Chrome 公网形态 E2E 通过：A 为 3/3 后漏学 0/3，B 始终 0；刷新、手记 3 条、dialog 焦点/Escape、375px、控制台均通过。详见 `docs/13_公网Demo部署与独立访客验收报告.md`。

仍需人工复核：真实手机软键盘、屏幕阅读器朗读顺序、桌面浏览器逐键主流程，以及正式录屏文件。自动化结果不能替代这些人工体验检查，也不代表项目已有公开部署地址。

## 清洁打包

已有 Git 提交时优先使用 `git archive`；它只打包已跟踪文件，不会带入 `.venv`、`node_modules`、`dist`、pytest 临时库、`.env` 或 SQLite 运行数据。

```powershell
# 项目根目录；先确认 .gitignore 和 staged 内容
git init
git add .
git status --short
git commit -m "feat: finalize SparkLab v0.2 demo"

# 输出到项目目录之外，避免压缩包把自己再次打包
git archive --format=zip --output=..\SparkLab_v0.2-source.zip HEAD
tar.exe -tf ..\SparkLab_v0.2-source.zip
```

检查压缩包清单时，应保留源码、测试、`package.json`、`package-lock.json`、`requirements.txt`、README、docs 与必要截图；不得出现 `.venv`、`node_modules`、`frontend/dist`、`backend/.pytest-tmp`、`*.sqlite3`、`.env`、缓存或真实密钥。不要直接“右键压缩”整个工作区。

若尚未初始化 Git，使用 `docs/11_最终交付验收与人工检查清单.md` 中经过本轮实测的 PowerShell 暂存目录方案；它会显式排除依赖、缓存、运行数据和 `delivery/`，并在压缩后解压复核。

## API

| 方法 | 路径 | 行为 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/today` | 恢复 `not_started / attempted / completed`；未揭晓不含答案 |
| GET | `/api/progress` | 服务端计算 streak、累计天数与本周星轨 |
| POST | `/api/tasks/{task_key}/attempt` | 首次选择落 `daily_attempts`；同选项幂等，不同选项 409 |
| POST | `/api/tasks/{task_key}/complete` | body 只收 `reflection`；读取已有 attempt 并幂等完成 |
| GET | `/api/history?limit=7` | 最近真实完成记录，只读且不穿越参考日 |
| POST | `/api/demo/reset` | 公网 Demo 中只清除当前签名匿名访客记录；带同源与限流校验 |
| POST | `/api/dev/reset` | 仅本地 Demo 开关同时为 true 且非公网模式时注册 |

Demo 模式下，上述日期相关接口可附 `?demo_date=YYYY-MM-DD`；可模拟范围为服务器真实北京时间前后 30 天。

## 数据规则

- 北京时间自然日唯一任务；`2026-11-05` 固定映射苹果题，同日刷新不换题。
- `daily_attempts` 与 `daily_completions` 分表；事务与 UNIQUE 共同保证一天一次。
- 反思去首尾空格后按 Python Unicode code point 计 6–120 字符，不进行 AI 评分。
- 错误猜想会明确说明不同，但同样能完成并点亮星星。
- 网络失败不伪成功；前端保留选择/反思供重试，刷新从数据库恢复。

更完整的取舍见 [设计说明](docs/design-rationale.md)，简版录屏步骤见 [演示脚本](docs/demo-script.md)，正式 90 秒镜头与解说见 [演示分镜](docs/10_正式演示分镜与解说词.md)。

