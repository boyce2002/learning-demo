# SparkLab Step 7｜真实公网部署与最终提交清单

**状态：** Step 6 已有安全改造及本地 Docker 验收；Step 7 需要真实 Git 仓库、Render 账号、HTTPS URL 和公网复验。在实际完成前，绝不能宣称公网已上线。

## 0. 现有证据（2026-11-08 独立核对）

- 上传源码包：`SparkLab_v0.2_public_demo_source.zip`；SHA-256 为 `D64333233C957D1F55C070FA12D02E2367D9E7B35C4A3665F6106806E8FAAC45`。
- ZIP 共有 79 个文件，包含 `Dockerfile`、`render.yaml`、`docs/12_简短产品设计说明_提交版.md`、`docs/13_公网Demo部署与独立访客验收报告.md`、`docs/14_在线Demo评审体验指南.md`。
- 独立重新执行 `cd backend; python -m pytest -q`：33 passed。未独立复跑 npm/Docker/Chrome 云端验证；本地 Windows 结果来自 Codex 的 Step 6 报告。
- `render.yaml` 使用 `runtime: docker`、`plan: 0.5c-512mb`、`SESSION_SECRET: generateValue: true`、`disk: /data`，字段与 Render 官方文档一致。

## 1. 用户在账号侧完成（需本人明确授权）

1. 准备 GitHub 账号与 Git 软件。创建一个空仓库，建议命名 `sparklab-demo`，可选择 Private。**不要上传 ZIP 当作唯一仓库文件**，应将解压后的项目文件作为仓库根目录内容，保证根目录含 `Dockerfile` 和 `render.yaml`。
2. 在本机项目根目录打开 PowerShell。确认不存在密钥/SQLite/依赖；执行：

   ```powershell
   git init
   git branch -M main
   git status --short
   git add .
   git status --short
   git diff --cached --name-only
   git commit -m "feat: prepare SparkLab public demo"
   git remote add origin https://github.com/<YOUR_USER>/sparklab-demo.git
   git push -u origin main
   ```

   把 `<YOUR_USER>` 替换为自己的 GitHub 用户名。远程仓库若不是空仓库，先检查历史再决定是否推送；禁止强推覆盖他人内容。不要把 Token、Cookie、`SESSION_SECRET`、`.env`、SQLite、`node_modules`、`.venv` 或 `dist` 提交。
3. 登录 [Render Dashboard](https://dashboard.render.com/)，选择 **New → Blueprint**，授权访问刚创建的 GitHub 仓库，选中包含 `render.yaml` 的分支。
4. **在支付确认前核对费用与资源**：Web Service `0.5c-512mb` 为付费计划，`/data` 的 1 GB 持久磁盘另收费；按 Render 官网当前公开标价约 **$7.25/月起**（不含可能的流量等额外费用）。确认自己愿意使用付费计划后再创建，切勿误选会丢失 SQLite 数据的免费无磁盘运行方式。
5. 在 Render 配置预览中确认：`PUBLIC_DEMO_ENABLED=true`、`DEMO_MODE=true`、`VISITOR_RESET_ENABLED=true`、`DEMO_RESET_ENABLED=false`、`COOKIE_SECURE=true`、`DATABASE_PATH=/data/sparklab.sqlite3`、`FRONTEND_DIST_PATH=/app/frontend/dist`。`SESSION_SECRET` 必须由 Render 生成，不能复制到 Git 仓库或聊天中。一个服务、一个实例，磁盘挂载为 `/data`。
6. 完成部署并复制平台生成的 **真实** `https://...onrender.com` URL。只有看到 Deploy 状态 Live 且首页能访问才进入复验；不要猜测或编造 URL。

## 2. 上线后由 Codex 执行真实验证

部署前复核 `README.md`、`render.yaml`、`backend/app/visitor.py`、`security.py`、`routes.py`、`services.py`、`frontend/src/api/client.ts`、`scripts/e2e-public-demo.mjs`；列出真实文件路径和函数。

### 基础检查

```powershell
$env:SPARKLAB_URL = "https://<actual-service>.onrender.com"
Invoke-WebRequest "$env:SPARKLAB_URL/api/health" | Select-Object StatusCode, Content
node .\scripts\e2e-public-demo.mjs
```

- HTTPS 有效，首页 200、CSS/JS 加载，`/api/health` 200。
- `/docs`、`/openapi.json`、`/api/dev/reset` 不可访问（404）。
- Cookie `Secure`、`HttpOnly`、`SameSite=Lax`，并按真实访客隔离。
- 浏览器 A 经 UI 完成 D、D+1、D+2：streak=3、累计=3；D+4 streak=0，累计仍为3。
- 全新浏览器 B 保持自己的 0 条记录；A reset 不影响 B。注意不要在同一普通浏览器配置中的两个标签页测试“不同访客”：它们共享 Cookie。
- A 刷新后记录恢复，星光手记与反思正确显示；375px 无横向滚动；常见控制台错误和触控体验复核。
- 原点及跨站写入、限流至少做非破坏性检查；不得在真实评审服务上执行破坏其他访客记录的操作。
- 在 Render 控制台进行 **有意触发的服务重启**，验证 A 原 Cookie 的完成状态和反思仍在。**不要删除持久磁盘或重置 SESSION_SECRET**。

### 通过后才能最终放行

- 实际 HTTP 结果、测试时间、两个独立会话的验证输出与截图写入 `docs/16_真实公网部署与复验报告.md`。
- 把真实 URL 填入 `docs/12_简短产品设计说明_提交版.md`、`docs/14_在线Demo评审体验指南.md`。用户最后提交的是**真实 Demo HTTPS 链接 + 简短说明文档**，不是把 GitHub/Render Dashboard 链接当 Demo 链接。
- 更新文档需要再次 `git add/commit/push`，Render 可能自动重部署；重部署后至少复核主页、health、Cookie 和持续化记录。请避免泄露任何密钥和隐私数据。
- 如云端失败，应给出真实日志和定位步骤，**不得把本地通过描述为公网通过**。

## 3. 可能的上线阻塞与处理

- **Render 要求付费信息**：属于账号侧授权，不能由 Codex 自动同意付款；说明当前阻塞及其他合适的托管备选，不擅自降低持久化要求。
- **Git remote / GitHub 登录失败**：由用户完成 GitHub 登录或凭据授权；禁止把密码/Token写入源码。
- **部署成功但状态丢失**：检查 `/data` 是否为真实持久磁盘、`DATABASE_PATH` 是否一致、服务是否多实例及 `SESSION_SECRET` 是否保持稳定。
- **Cookie 每次刷新变化**：检查 HTTPS、`Secure` 属性和前后端是否真正同域。
- **Git 提交了旧图或者隐藏的敏感文件**：先检查 staged 清单和仓库历史；若敏感信息已经曝光，必须轮换相应秘密，不能只做后续文件删除。

## 4. 交给 Codex 的执行指令

> 现在进入 SparkLab Step 7：真实公网部署和最终交付。请先核对本项目真实文件，读取本清单，并检查 Git 状态与 Render 授权是否可用。不得重复重构已通过的业务功能。若 GitHub/Render 的账号授权或付费确认缺失，请明确列出需要我亲自执行的 UI 步骤，等待我完成这些外部授权；不要声称后台部署已经开始或产出虚构地址。授权具备后，协助完成 Git push、Render Blueprint 配置审核、真实 HTTPS 首次访问、A/B 独立会话与持久磁盘重启复验。所有可自动化验证必须实际运行并记录证据；最终新增 `docs/16_真实公网部署与复验报告.md`，回填第 12、14 号文档中的真实网址，输出 GO/NO-GO。禁止提交密钥、数据库、Cookie、依赖目录、临时测试产物或用户数据。

## 5. 最终提交模板

**在线 Demo：** `https://<真实部署地址>`  
**设计说明：** `docs/12_简短产品设计说明_提交版.md`（正式版）  
**模拟数据声明：** 本 Demo 使用人工预置题库。演示时间舱模拟学习日期，记录来自当前匿名访客的真实操作，仅用于展示连续学习机制，不代表真实学生的长期学习数据。

> 设计宗旨：先猜想、再揭晓、最后总结，让学生因为主动思考得到正向反馈；成长星轨鼓励坚持，星光手记呈现学习积累。

## 官方参考

- Blueprint YAML： https://render.com/docs/blueprint-spec
- 持久磁盘： https://render.com/docs/disks
- 部署说明： https://render.com/docs/deploys
- 价格： https://render.com/pricing
