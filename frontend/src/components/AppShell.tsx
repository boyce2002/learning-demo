import type { ReactNode } from "react";
import { copy } from "../content/copy";

interface AppShellProps {
  children: ReactNode;
  isDemoMode?: boolean;
}

export function AppShell({ children, isDemoMode = false }: AppShellProps) {
  return (
    <div className="app-shell">
      <div className="star-field" aria-hidden="true" />
      <header className="brand-bar">
        <a className="brand-lockup" href="#main-content" aria-label="微光实验室首页">
          <span className="brand-mark" aria-hidden="true">✦</span>
          <span>
            <strong>{copy.brand}</strong>
            <small>{copy.brandEn}</small>
          </span>
        </a>
        <div className="user-badge">
          <span className="user-dot" aria-hidden="true" />
          {copy.demoUser}
        </div>
      </header>
      {isDemoMode && (
        <div className="demo-mode-notice" role="status">
          演示体验｜题目为人工预置；学习日期和成长记录可模拟，不代表真实学生数据。
        </div>
      )}
      {children}
      <footer className="site-footer">
        <span>{copy.slogan}</span>
        <span>匿名访客独立记录 · 预置人工题库</span>
      </footer>
    </div>
  );
}

