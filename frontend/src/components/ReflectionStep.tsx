import { copy } from "../content/copy";

interface ReflectionStepProps {
  prompt: string;
  value: string;
  isSubmitting: boolean;
  error: string | null;
  onChange: (value: string) => void;
  onBack: () => void;
  onComplete: () => void;
}

export function ReflectionStep({
  prompt,
  value,
  isSubmitting,
  error,
  onChange,
  onBack,
  onComplete,
}: ReflectionStepProps) {
  const length = Array.from(value.trim()).length;
  const valid = length >= 6 && length <= 120;
  const hint = length > 120 ? "最多 120 个字符，试着再精炼一点。" : "至少写 6 个字符，再点亮星星。";

  return (
    <section className="challenge-card step-card reflect-card" aria-labelledby="reflect-title">
      <button className="text-button back-button" type="button" onClick={onBack} disabled={isSubmitting}>
        <span aria-hidden="true">←</span> 返回知识卡
      </button>
      <p className="step-indicator">{copy.reflectStage}</p>
      <h2 id="reflect-title">{copy.reflectHeading}</h2>
      <p className="reflect-subtitle">{copy.reflectSubtitle}</p>
      <blockquote>{prompt}</blockquote>
      <div className="textarea-heading">
        <label htmlFor="reflection">{copy.reflectLabel}</label>
        <span className={length > 120 ? "count count--error" : "count"}>{length} / 120 字符</span>
      </div>
      <textarea
        id="reflection"
        value={value}
        rows={5}
        disabled={isSubmitting}
        aria-describedby="reflection-hint"
        aria-invalid={length > 120}
        placeholder={copy.reflectPlaceholder}
        onChange={(event) => onChange(event.target.value)}
      />
      <p id="reflection-hint" className={length > 120 ? "field-hint field-hint--error" : "field-hint"}>
        {valid ? "长度合适，可以点亮今天的星星。" : hint}
      </p>
      {error && <p className="inline-error" role="alert">{error}</p>}
      <button className="primary-button" type="button" disabled={!valid || isSubmitting} onClick={onComplete}>
        {isSubmitting ? copy.completing : copy.complete}
        {!isSubmitting && <span aria-hidden="true">✦</span>}
      </button>
    </section>
  );
}

