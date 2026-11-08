# SparkLab 设计与工程说明

## 目标与闭环

SparkLab 把“主动学习”落实为一次五分钟内可完成的行为链：先做猜想，后看人工预写的准确解释，再用自己的话留下 6–120 字反思，最后才点亮星星。错误选择不会扣分或失去星星；页面会诚实说明猜想与答案不同，同时尊重探索过程。反思只校验长度，不用 LLM 做虚假语义评分。

## 视觉与体验

页面使用深蓝紫夜幕、月白知识卡和香槟金星轨。夜空只保留低对比 CSS 星点，动效只用于状态过渡和首次完成的 550ms 点亮，避免粒子爆炸、恐惧式断签和幼态奖励。桌面以任务/成长双栏建立主次，≤900px 堆叠；375px 实测无横向溢出。原生 radio、textarea、可见 focus、状态文字和 `prefers-reduced-motion` 支持键盘与减少动效偏好。

## 真实数据与持久化

SQLite 是唯一业务状态。揭晓时先写 `daily_attempts` 并锁定首次选择；完成接口只接收 reflection，再读取同日 attempt 写 `daily_completions`。两张表分别以 `(user_id, local_date)` UNIQUE，加上 `BEGIN IMMEDIATE`，保证重复/并发提交不覆盖首次内容。today 可恢复三个 phase；进度、累计、周星轨都由后端按北京时间与参考日计算，前端不做乐观 +1。

## Demo 与安全边界

用户固定为 `demo_student`，题库为 7 道人工种子。只有 `DEMO_MODE=true` 才接受模拟日期；只有同时设置 `DEMO_RESET_ENABLED=true` 才注册 reset。UI 会明确标记“演示用户/模拟数据”。公开链接会共享固定用户记录，因此默认建议交演示视频；未实现会话隔离时不得开放共享 reset。

## 已验证与待人工复核

- 2026-11-07 Step 5 本轮已验证：pytest `25 passed in 21.35s`（T01–T19，含并发和时区）；独立 TypeScript 检查通过；Vite 6.4.5 production build 通过（42 modules，968ms）；`npm ci` 与显式 `npm audit` 均为 0 漏洞。正常模式真实启动后 `/api/health` 为 200、两张 SQLite 表自动初始化、`demo_date` 为 403、reset 为 404。
- 系统 Chrome headless 在 375px 通过真实 UI 和 DemoToolbar 跑过错误猜想闭环、刷新恢复、连续三天、漏学归零、历史倒序/过去视角、快速日期切换、手记快速开关、历史慢请求竞态和完成请求断网重试，根节点 `scrollWidth=375`。
- 手记键盘验收已自动化执行：打开后焦点进入关闭按钮，Shift+Tab/Tab 在两个可操作元素间首尾循环，Escape 关闭并将焦点还给“查看我的星光手记”；连续打开关闭 3 次无异常。监听器由 React effect 挂载并在卸载时清理。
- 待人工复核：真实手机软键盘、屏幕阅读器朗读顺序、桌面浏览器逐键走完整 S1–S6、不同浏览器的视觉细节、60–90 秒正式录屏。当前没有公开部署 URL。

