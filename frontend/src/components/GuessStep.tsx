import { copy } from "../content/copy";
import type { PublicTask } from "../types";

interface GuessStepProps {
  task: PublicTask;
  selectedOption: string | null;
  isSubmitting: boolean;
  error: string | null;
  onSelect: (option: string) => void;
  onReveal: () => void;
}

export function GuessStep({
  task,
  selectedOption,
  isSubmitting,
  error,
  onSelect,
  onReveal,
}: GuessStepProps) {
  return (
    <section className="challenge-card step-card" aria-labelledby="guess-title">
      <p className="step-indicator">{copy.guessStage}</p>
      <h2 id="guess-title">{copy.guessHeading}</h2>
      <p className="step-question">{task.question}</p>
      <fieldset className="answer-options">
        <legend className="sr-only">选择一个最接近的猜想</legend>
        {task.options.map((option, index) => {
          const checked = selectedOption === option.key;
          return (
            <label className={`answer-option${checked ? " answer-option--selected" : ""}`} key={option.key}>
              <input
                type="radio"
                name="guess"
                value={option.key}
                checked={checked}
                disabled={isSubmitting}
                onChange={() => onSelect(option.key)}
              />
              <span className="option-letter">{String.fromCharCode(65 + index)}</span>
              <span className="option-label">{option.label}</span>
              <span className="option-check" aria-hidden="true">{checked ? "✓" : ""}</span>
            </label>
          );
        })}
      </fieldset>
      <p className="gentle-hint"><span aria-hidden="true">◇</span>{copy.guessHint}</p>
      {error && <p className="inline-error" role="alert">{error}</p>}
      <button
        className="primary-button"
        type="button"
        disabled={!selectedOption || isSubmitting}
        onClick={onReveal}
      >
        {isSubmitting ? copy.revealing : copy.reveal}
        {!isSubmitting && <span aria-hidden="true">→</span>}
      </button>
      {!selectedOption && <p className="button-help">选一个你最接近的猜想</p>}
    </section>
  );
}

