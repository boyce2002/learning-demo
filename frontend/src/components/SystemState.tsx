import { copy } from "../content/copy";

export function LoadingState() {
  return (
    <main id="main-content" className="dashboard-grid" aria-busy="true">
      <p className="sr-only" role="status">{copy.loading}</p>
      <div className="challenge-card skeleton-card" aria-hidden="true">
        <span /><span /><span /><span />
      </div>
      <div className="progress-panel skeleton-card" aria-hidden="true">
        <span /><span /><span />
      </div>
    </main>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <main id="main-content" className="single-state">
      <section className="challenge-card error-card" role="alert">
        <span className="error-icon" aria-hidden="true">◇</span>
        <p className="step-indicator">CONNECTION PAUSED</p>
        <h1>{copy.loadError}</h1>
        <p>{message}</p>
        <button className="primary-button" type="button" onClick={onRetry}>{copy.retry}</button>
      </section>
    </main>
  );
}
