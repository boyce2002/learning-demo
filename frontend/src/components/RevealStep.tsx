import { copy } from "../content/copy";
import type { AttemptDetail, PublicTask } from "../types";

interface RevealStepProps {
  task: PublicTask;
  attempt: AttemptDetail;
  onReflect: () => void;
}

function optionLabel(task: PublicTask, key: string) {
  return task.options.find((option) => option.key === key)?.label || key;
}

export function RevealStep({ task, attempt, onReflect }: RevealStepProps) {
  return (
    <section className="challenge-card step-card reveal-card" aria-labelledby="reveal-title">
      <p className="step-indicator">{copy.revealStage}</p>
      <div className={`result-icon${attempt.was_correct ? " result-icon--correct" : ""}`} aria-hidden="true">
        {attempt.was_correct ? "✦" : "◇"}
      </div>
      <h2 id="reveal-title">{attempt.was_correct ? copy.correctTitle : copy.incorrectTitle}</h2>
      <p className="result-feedback">{attempt.feedback}</p>
      <dl className="answer-comparison">
        <div>
          <dt>{copy.yourGuess}</dt>
          <dd>{optionLabel(task, attempt.selected_option)}</dd>
        </div>
        <div className="fact-answer">
          <dt>{copy.rightAnswer}</dt>
          <dd><span aria-hidden="true">✓</span>{optionLabel(task, attempt.correct_option)}</dd>
        </div>
      </dl>
      <div className="explanation-box">
        <h3>{copy.explanationTitle}</h3>
        <p>{attempt.explanation}</p>
      </div>
      <div className="takeaway-box">
        <span aria-hidden="true">✦</span>
        <div><strong>{copy.takeawayTitle}</strong><p>{attempt.takeaway}</p></div>
      </div>
      <button className="primary-button" type="button" onClick={onReflect}>
        {copy.reflect}<span aria-hidden="true">→</span>
      </button>
    </section>
  );
}

