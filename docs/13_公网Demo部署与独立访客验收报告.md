# SparkLab Step 6｜公网 Demo 部署与独立访客验收报告

**实施日期：** 2026-11-08（Asia/Shanghai）  
**当前公网 URL：** 无。当前环境没有 Git 仓库、Render/Railway/Fly CLI、云平台令牌或已授权账号，未把配置完成描述为上线成功。  
**结论：** 公网最小改造与本地生产形态验收为 GO；真实 HTTPS 云部署与公网复验在获得账号授权前为 NO-GO。

## 1. 改了什么

### 后端匿名会话与隔离

- `backend/app/visitor.py`（新增）
  - `VisitorSessionManager.encode/decode/resolve`：生成 128-bit 随机访客 ID，用 HMAC-SHA256 和服务端密钥签名；校验签名、签发时间与七天有效期，过半有效期自动重签。
  - Cookie 为 `HttpOnly`、公网 `Secure`、`SameSite=Lax`、`Path=/`；浏览器不能通过请求体或查询参数指定可信 user id。
- `backend/app/services.py`
  - `get_today`、`record_attempt`、`complete_day`、`get_progress`、`get_history` 全部显式接收已验证 `visitor_id`，每条 SQL 均按访客过滤。
  - `reset_visitor` 只删除当前访客两张表的数据；原有题目、事务、UNIQUE、反思校验、幂等和 streak 算法未改。
- `backend/app/security.py`（新增）
  - `is_trusted_write` 拒绝不可信 `Origin` 和 `Sec-Fetch-Site: cross-site`。
  - `InMemoryRateLimiter`：普通写入默认每访客 60 次/分钟，reset 默认 3 次/小时。
- `backend/app/routes.py`
  - 所有业务路由通过依赖取得签名访客身份；POST 在进入业务层前执行来源和频率校验。
  - 公网仅注册 `/api/demo/reset`；`/api/dev/reset` 只可能出现在非公网本机 Demo。
- `backend/app/config.py`
  - 新增公网模式、访客 reset、签名密钥、Cookie、允许来源、请求体上限、限流和静态目录配置。
  - `PUBLIC_DEMO_ENABLED=true` 且 `SESSION_SECRET` 少于 32 字符时拒绝启动。
- `backend/app/main.py`
  - 公网关闭 `/docs`、`/redoc`、`/openapi.json`；未知 `/api/*` 固定返回 JSON 404。
  - 写请求实际读取并限制为 4096 bytes；API 加 `no-store`、`nosniff` 与同源 referrer policy。
  - 可由同一 FastAPI 进程挂载 Vite `dist`，实现页面、Cookie、API 同域。

### 前端与体验声明

- `frontend/src/api/client.ts`：显式 `credentials: "same-origin"`；reset 改为 `/api/demo/reset`。
- `frontend/src/App.tsx`：首次 today/progress 顺序请求，避免无 Cookie 时两个并发请求各获不同身份；reset 确认文案改为当前匿名访客。
- `frontend/src/types.ts`：不再把 UI 身份写死为 `demo_student`。
- `frontend/src/components/AppShell.tsx`、`DemoToolbar.tsx`、`ProgressPanel.tsx`：明确“人工预置、日期/成长可模拟、非真实学生数据”和“当前匿名访客独立记录”。
- `frontend/src/styles/global.css`：只为较长演示声明增加最大宽度与行高，未改变视觉体系。

### 部署与验证资产

- `Dockerfile`：Node 22 构建 Vite，Python 3.12 运行 FastAPI，默认单进程同域服务。
- `render.yaml`：Render `0.5c-512mb` Web Service、`/data` 1 GB 持久磁盘、平台生成 `SESSION_SECRET`、全局 reset 关闭。
- `.dockerignore`、`.env.example`、`.gitignore`：排除密钥、数据库、依赖、缓存和构建物。
- `scripts/e2e-public-demo.mjs`：仅使用 Node 标准能力和系统 Chrome CDP，创建 A/B 两个独立浏览器会话并验收完整流程。
- `backend/tests/test_public_demo_security.py`：新增 8 项公网安全场景；原 25 项测试全部保留。

## 2. 为什么修改

原实现把所有 SQL 绑定到 `DEMO_USER_ID = "demo_student"`。公开后，任一访客都能看到、覆盖或重置同一份学习记录，这是阻断上线的问题。仅由前端生成 user id 不能作为安全边界，因为请求可以伪造。

本轮把身份信任点放到后端：随机 ID 只有通过服务端密钥签名后才生效。数据表原本已有 `(user_id, local_date)` 唯一约束和索引，因此不需要改表或清空旧数据库。旧 `demo_student` 数据原样保留，新匿名会话不会查询它；密钥轮换只会让浏览器开始新会话，不会删除旧行。

CSRF 采用同域 HTTPS、SameSite=Lax、写请求 Origin/Sec-Fetch-Site 校验的组合。该 Demo 没有账号或高价值权限，因此没有额外引入 token UI；若未来出现登录或跨域前端，应升级为显式 CSRF token。CORS 仅用于本地 Vite 开发，不被当作 CSRF 防线。

## 3. 实现效果

| 项目 | 修改前 | 修改后 |
|---|---|---|
| 访客身份 | 全局固定 `demo_student` | 后端签名随机匿名会话 |
| 进度与手记 | 所有人共享 | today/attempt/completion/progress/history 全隔离 |
| reset | 本机开关可删除固定用户全量 | 公网只删当前访客；全局 route 不注册 |
| 模拟日期 | 全局固定用户的参考日 | 只作用于当前访客查询与写入 |
| 前后端 | Vite 与 FastAPI 两端口 | 生产单域：FastAPI 托管 `dist` + `/api` |
| SQLite | 本地相对路径 | 公网写 `/data` 持久磁盘，容器重启可恢复 |
| 调试面 | 公网默认可见 FastAPI docs | 公网关闭 docs/redoc/openapi |

## 4. 实际测试证据

### 后端

```powershell
python -m venv .venv
$env:NO_PROXY='*'; $env:no_proxy='*'
.\.venv\Scripts\python.exe -m pip --isolated install -r .\backend\requirements.txt
Set-Location .\backend
..\.venv\Scripts\python.exe -m pytest -q
```

- 锁定依赖安装成功。
- 完整 pytest：`33 passed in 31.59s`。
- 新增覆盖：A/B 会话 today/progress/history 隔离、user_id 注入无效、当前访客 reset、Cookie 篡改、过期与重签、跨站写入拒绝、请求体上限、Cookie 安全属性。
- 原并发 completion 测试改为显式同一 visitor，仍验证一条新增、一条幂等返回。

### 前端

```powershell
Set-Location .\frontend
npm.cmd ci
npm.cmd exec tsc -- -b
npm.cmd run build
npm.cmd audit --json
```

- `npm ci`：added 70 packages，audited 71 packages，0 vulnerabilities。
- TypeScript：退出码 0。
- Vite 6.4.5：42 modules transformed，2.13s。
- npm audit：info/low/moderate/high/critical 均为 0。

### 单域生产形态与 Docker

```powershell
docker build --tag sparklab-demo:step6 .
```

- 镜像构建成功；镜像内部再次完成 `npm ci`、42 模块 build 和 Python 锁定依赖安装。
- 本机生产形态 smoke：`/` 200 且包含 `#root`；`/api/health` 200；today 200 且 Cookie 包含 HttpOnly/SameSite；attempt 200；跨站 attempt 403；访客 reset 200；`/docs`、`/api/dev/reset` 均 404。
- Docker 独立测试卷写入完成记录后，删除并重新创建容器、复用同一卷；`phase=completed` 与原反思均恢复，证明数据不依赖容器临时层。
- 测试容器、测试卷和临时 Cookie 已删除；未写入项目运行数据库。

### 两个真实浏览器会话

```powershell
$env:SPARKLAB_URL='http://127.0.0.1:8766'
node .\scripts\e2e-public-demo.mjs
```

最终输出 `"passed":true`：

- A 通过真实 UI 完成 D、D+1、D+2：streak 3、累计 3；D+4：streak 0、累计仍 3。
- A 刷新后 `phase=completed`；手记显示 3 条，焦点进入 dialog，Escape 关闭后归还按钮。
- B 使用独立 Chrome 用户目录，累计始终为 0。
- 设备指标 375×812：`innerWidth=375`、`scrollWidth=375`。
- console error 0，page exception 0。

首次自动化中出现且已如实处理的问题：受限沙箱使 Python/Node 对 G 盘 `realpath` 报权限错误，改在正常 Windows 权限上下文重跑；系统代理导致 pip 失败，使用 `NO_PROXY=*` 后成功；Docker Desktop 初始未运行，启动后镜像成功；浏览器脚本首次被 Chrome Crashpad 临时文件 `EBUSY` 干扰，修复退出等待后重跑；另一次刷新断言误把 completed 恢复页当首页，修正真实 UI 预期后最终通过。没有删除测试或降低业务断言。

## 5. 安全策略与已知限制

- `SESSION_SECRET` 不在仓库中；Render Blueprint 用 `generateValue: true` 生成。
- Cookie 保存的是随机访客 ID、签发时间和签名，不含反思或密钥；反思正文不写日志。
- 限流器为进程内实现；Render 持久磁盘限定单实例，二者当前一致。多实例部署必须改为共享限流与可靠数据库。
- SQLite 持久磁盘不能横向扩容，部署时会有短暂停机；适合低流量面试 Demo，不是多租户生产方案。
- 匿名会话无账号恢复：清 Cookie、换浏览器、会话过期或密钥轮换都会看到新体验；旧数据不会串给新访客。
- 未做真实手机软键盘、NVDA/VoiceOver、跨公网地区延迟或云平台重启验收。

## 6. 部署步骤与当前阻塞

`render.yaml` 已按 2026-11-08 Render 官方 Blueprint 字段核对：Docker runtime、`generateValue`、`disk.name/mountPath/sizeGB` 与 `0.5c-512mb` 均为有效配置。持久磁盘只能用于付费 Web Service，不能改为免费临时文件系统。

仍需账号所有者完成：

1. 初始化/连接 Git 仓库并推送清洁源码。
2. 登录 Render，New Blueprint → 选择仓库 → 审核付费 `0.5c-512mb` 与 1 GB 磁盘。
3. 创建服务，等待真实 HTTPS URL。
4. 按本文 smoke 与 A/B 浏览器脚本对真实 URL 重跑；确认平台重启后记录恢复。
5. 把真实 URL 回填本文、`docs/12_简短产品设计说明_提交版.md` 和投递材料。

## 7. GO / NO-GO

- 源码匿名隔离、安全边界、生产镜像：**GO**。
- 本机单域 Docker 与浏览器演示：**GO**。
- 直接公开固定用户 Demo：**NO-GO**（已被新架构替代）。
- 当前声称“公网已上线”：**NO-GO**，因为没有云账号授权和真实 HTTPS URL。
- 获得账号授权并完成 URL 复验后：**Conditional GO**。
