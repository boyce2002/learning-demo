import { copy } from "../content/copy";
import type { CompletionDetail, ProgressResponse } from "../types";

interface CompletionStepProps {
  completion: CompletionDetail;
  progress: ProgressResponse;
  animate: boolean;
  onHome: () => void;
  onReview: () => void;
}

export function CompletionStep({ completion, progress, animate, onHome, onReview }: CompletionStepProps) {
  return (
    <section
      className={`challenge-card step-card completion-card${animate ? " completion-card--fresh" : ""}`}
      aria-labelledby="done-title"
      aria-live="polite"
    >
      <div className="success-star" aria-hidden="true">
        <span>✦</span>
        <i /><i /><i /><i />
      </div>
      <p className="step-indicator">{copy.doneEyebrow}</p>
      <h2 id="done-title">{copy.doneTitle}</h2>
      <p className="done-subtitle">{copy.doneSubtitle}</p>
      <div className="saved-reflection">
        <span>{copy.doneReflection}</span>
        <blockquote>“{completion.reflection}”</blockquote>
      </div>
      <div className="done-stats" aria-label="完成后的真实进度">
        <p><strong>{progress.streak_days}</strong><span>连续探索 / 天</span></p>
        <span className="stats-divider" aria-hidden="true" />
        <p><strong>{progress.total_completed_days}</strong><span>累计点亮 / 天</span></p>
      </div>
      <p className="done-warm">{copy.doneWarm}</p>
      <div className="button-row">
        <button className="primary-button" type="button" onClick={onHome}>{copy.home}</button>
        <button className="secondary-button" type="button" onClick={onReview}>{copy.reviewKnowledge}</button>
      </div>
    </section>
  );
}

