import type { RefObject } from "react";
import type { ProgressResponse } from "../types";
import { StarOrbit } from "./StarOrbit";

interface ProgressPanelProps {
  progress: ProgressResponse;
  onOpenJournal?: () => void;
  journalButtonRef?: RefObject<HTMLButtonElement>;
}

export function ProgressPanel({ progress, onOpenJournal, journalButtonRef }: ProgressPanelProps) {
  const message =
    progress.streak_days === 0
      ? "每一天，都可以是新的开始。"
      : progress.streak_days === 1
        ? "第一颗星，已经亮起来了。"
        : "你正在把好奇心变成习惯。";

  return (
    <aside className="progress-panel" aria-labelledby="progress-title">
      <div className="panel-glow" aria-hidden="true" />
      <p className="panel-kicker">YOUR ORBIT</p>
      <h2 id="progress-title">你的成长星轨</h2>
      <div className="progress-summary">
        <div>
          <span>连续探索</span>
          <strong>{progress.streak_days}<small> 天</small></strong>
        </div>
        <div>
          <span>累计点亮</span>
          <strong>{progress.total_completed_days}<small> 天</small></strong>
        </div>
      </div>
      <StarOrbit days={progress.week_days} />
      <p className="progress-message"><span aria-hidden="true">✦</span>{message}</p>
      {onOpenJournal && (
        <button ref={journalButtonRef} className="journal-button" type="button" onClick={onOpenJournal}>
          查看我的星光手记 <span aria-hidden="true">→</span>
        </button>
      )}
      <p className="progress-source">数据来自当前匿名访客的独立演示记录</p>
    </aside>
  );
}
