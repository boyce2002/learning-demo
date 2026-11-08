import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const baseUrl = process.env.SPARKLAB_URL || "http://127.0.0.1:8766";
const chromeCandidates = [
  process.env.CHROME_PATH,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
].filter(Boolean);
const chromePath = chromeCandidates.find(existsSync);
if (!chromePath) throw new Error("Chrome/Edge executable was not found.");

class CdpClient {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.events = [];
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.id) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(message.error.message));
        else pending.resolve(message.result);
      } else {
        this.events.push(message);
      }
    };
  }

  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolveOpen, rejectOpen) => {
      socket.onopen = resolveOpen;
      socket.onerror = () => rejectOpen(new Error("CDP WebSocket connection failed."));
    });
    return new CdpClient(socket);
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolveCommand, rejectCommand) => {
      this.pending.set(id, { resolve: resolveCommand, reject: rejectCommand });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  async evaluate(expression) {
    const result = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.text || "Browser evaluation failed.");
    }
    return result.result.value;
  }

  close() {
    this.socket.close();
  }
}

const delay = (milliseconds) => new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds));

async function waitForValue(client, expression, timeoutMs = 10000) {
  const deadline = Date.now() + timeoutMs;
  let lastValue;
  while (Date.now() < deadline) {
    lastValue = await client.evaluate(expression);
    if (lastValue) return lastValue;
    await delay(100);
  }
  throw new Error(`Timed out waiting for: ${expression}; last=${JSON.stringify(lastValue)}`);
}

async function launchBrowser(label) {
  const profile = await mkdtemp(join(tmpdir(), `sparklab-${label}-`));
  const port = 9300 + Math.floor(Math.random() * 300);
  const process = spawn(
    chromePath,
    [
      "--headless=new",
      "--disable-gpu",
      "--disable-crash-reporter",
      "--no-first-run",
      "--no-default-browser-check",
      "--remote-debugging-address=127.0.0.1",
      `--remote-debugging-port=${port}`,
      `--user-data-dir=${profile}`,
      "--window-size=375,812",
      baseUrl,
    ],
    { stdio: "ignore" },
  );

  let target;
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const targets = await fetch(`http://127.0.0.1:${port}/json/list`).then((response) => response.json());
      target = targets.find((item) => item.type === "page");
      if (target) break;
    } catch {
      // Browser is still starting.
    }
    await delay(100);
  }
  if (!target) throw new Error(`Browser ${label} did not expose a page target.`);
  const client = await CdpClient.connect(target.webSocketDebuggerUrl);
  await client.send("Page.enable");
  await client.send("Runtime.enable");
  await client.send("Emulation.setDeviceMetricsOverride", {
    width: 375,
    height: 812,
    deviceScaleFactor: 1,
    mobile: true,
  });
  await client.send("Page.reload", { ignoreCache: true });
  await waitForValue(client, "document.readyState === 'complete'");
  await waitForValue(client, "document.body && document.body.innerText.includes('开始今天的探索')");
  return { client, process, profile };
}

function buttonExpression(label) {
  return `(() => { const button = [...document.querySelectorAll('button')].find((item) => item.textContent.includes(${JSON.stringify(label)})); if (!button || button.disabled) return false; button.click(); return true; })()`;
}

async function completeCurrentDay(client, reflection) {
  await waitForValue(client, buttonExpression("开始今天的探索"));
  await waitForValue(client, "document.querySelectorAll('input[type=radio]').length > 0");
  await client.evaluate("document.querySelector('input[type=radio]').click(); true");
  await waitForValue(client, buttonExpression("揭晓答案"));
  await waitForValue(client, buttonExpression("写下今天的发现"));
  await waitForValue(client, "Boolean(document.querySelector('textarea'))");
  await client.evaluate(`(() => { const field = document.querySelector('textarea'); const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set; setter.call(field, ${JSON.stringify(reflection)}); field.dispatchEvent(new Event('input', { bubbles: true })); return true; })()`);
  await waitForValue(client, buttonExpression("点亮今天的星星"));
  await waitForValue(client, "document.body.innerText.includes('今天的星星，亮了！')");
}

async function currentProgress(client) {
  return client.evaluate(`(async () => { const date = document.querySelector('input[type=date]')?.value; const suffix = date ? '?demo_date=' + encodeURIComponent(date) : ''; return fetch('/api/progress' + suffix).then((response) => response.json()); })()`);
}

const browsers = [];
try {
  const browserA = await launchBrowser("a");
  browsers.push(browserA);
  const browserB = await launchBrowser("b");
  browsers.push(browserB);

  await completeCurrentDay(browserA.client, "浏览器 A 完成了独立的第一天探索记录。 ");
  const firstProgress = await currentProgress(browserA.client);
  await browserA.client.send("Page.reload", { ignoreCache: true });
  await waitForValue(browserA.client, "document.body && document.body.innerText.includes('今天的星星，亮了！')");
  const restoredPhase = await browserA.client.evaluate("fetch('/api/today').then((response) => response.json()).then((data) => data.phase)");

  await waitForValue(browserA.client, buttonExpression("+1 天"));
  await waitForValue(browserA.client, "document.body.innerText.includes('开始今天的探索')");
  await completeCurrentDay(browserA.client, "浏览器 A 用自己的话记录了第二天的发现。 ");
  await waitForValue(browserA.client, buttonExpression("+2 天"));
  await waitForValue(browserA.client, "document.body.innerText.includes('开始今天的探索')");
  await completeCurrentDay(browserA.client, "浏览器 A 连续第三天留下了真实反思记录。 ");
  const threeDayProgress = await currentProgress(browserA.client);

  await waitForValue(browserA.client, buttonExpression("+4 天"));
  await waitForValue(browserA.client, "document.body.innerText.includes('开始今天的探索')");
  const gapProgress = await currentProgress(browserA.client);

  await waitForValue(browserA.client, buttonExpression("查看我的星光手记"));
  await waitForValue(browserA.client, "Boolean(document.querySelector('[role=dialog]'))");
  await waitForValue(browserA.client, "document.querySelectorAll('.journal-list > li').length === 3");
  const dialogState = await browserA.client.evaluate(`(() => ({ entries: document.querySelectorAll('.journal-list > li').length, focusInside: document.querySelector('[role=dialog]').contains(document.activeElement) }))()`);
  await browserA.client.evaluate("document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); true");
  await waitForValue(browserA.client, "!document.querySelector('[role=dialog]')");
  const focusReturned = await browserA.client.evaluate("document.activeElement?.classList.contains('journal-button')");

  const browserBProgress = await currentProgress(browserB.client);
  const viewport = await browserA.client.evaluate(`({ innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth })`);
  const consoleErrors = browserA.client.events.filter((event) => event.method === "Runtime.consoleAPICalled" && event.params.type === "error").length;
  const pageExceptions = browserA.client.events.filter((event) => event.method === "Runtime.exceptionThrown").length;

  const report = {
    firstProgress,
    restoredPhase,
    threeDayProgress,
    gapProgress,
    dialogState,
    focusReturned,
    browserBTotal: browserBProgress.total_completed_days,
    viewport,
    consoleErrors,
    pageExceptions,
  };
  const passed = firstProgress.total_completed_days === 1
    && restoredPhase === "completed"
    && threeDayProgress.streak_days === 3
    && threeDayProgress.total_completed_days === 3
    && gapProgress.streak_days === 0
    && gapProgress.total_completed_days === 3
    && dialogState.entries === 3
    && dialogState.focusInside
    && focusReturned
    && browserBProgress.total_completed_days === 0
    && viewport.innerWidth === 375
    && viewport.scrollWidth <= 375
    && consoleErrors === 0
    && pageExceptions === 0;
  console.log(JSON.stringify({ passed, ...report }));
  if (!passed) process.exitCode = 1;
} finally {
  for (const browser of browsers) {
    browser.client.close();
    const exited = new Promise((resolveExit) => browser.process.once("exit", resolveExit));
    browser.process.kill();
    await Promise.race([exited, delay(1500)]);
    const absoluteProfile = resolve(browser.profile);
    const absoluteTemp = resolve(tmpdir());
    if (absoluteProfile.startsWith(absoluteTemp) && absoluteProfile.includes("sparklab-")) {
      try {
        await rm(absoluteProfile, {
          recursive: true,
          force: true,
          maxRetries: 5,
          retryDelay: 200,
        });
      } catch {
        // A late Chrome crashpad handle must not hide browser assertion results.
      }
    }
  }
}
