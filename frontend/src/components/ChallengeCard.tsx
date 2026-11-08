import { copy } from "../content/copy";
import type { PublicTask } from "../types";

interface ChallengeCardProps {
  task: PublicTask;
  completed: boolean;
  onStart: () => void;
}

export function ChallengeCard({ task, completed, onStart }: ChallengeCardProps) {
  return (
    <section className="challenge-card challenge-card--home" aria-labelledby="challenge-title">
      <div className="card-topline">
        <span>{copy.todayLabel}</span>
        {completed ? <span className="complete-chip">今日已点亮</span> : <span aria-hidden="true">✦</span>}
      </div>
      <div className="challenge-content">
        <span className="category-chip">{task.category}</span>
        <h2 id="challenge-title">{task.title}</h2>
        <p className="challenge-question">{task.question}</p>
        <p className="challenge-intro">{copy.challengeIntro}</p>
      </div>
      <div className="challenge-meta">
        <span><span aria-hidden="true">◷</span> 约 {task.estimated_minutes} 分钟</span>
        <span>三步微探索</span>
      </div>
      <button className="primary-button" type="button" onClick={onStart}>
        {completed ? copy.review : copy.start}
        <span aria-hidden="true">→</span>
      </button>
      <p className="warm-note">「{copy.warmReminder}」</p>
    </section>
  );
}

