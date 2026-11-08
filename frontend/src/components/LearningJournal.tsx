import { useEffect, useRef } from "react";
import type { RefObject } from "react";
import type { HistoryEntry } from "../types";

interface LearningJournalProps {
  entries: HistoryEntry[];
  isLoading: boolean;
  error: string | null;
  onClose: () => void;
  returnFocusRef: RefObject<HTMLButtonElement>;
}

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

function displayDate(dateText: string) {
  const date = new Date(`${dateText}T00:00:00+08:00`);
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "long",
    day: "numeric",
    weekday: "short",
  }).format(date);
}

export function LearningJournal({
  entries,
  isLoading,
  error,
  onClose,
  returnFocusRef,
}: LearningJournalProps) {
  const dialogRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    const returnFocusElement = returnFocusRef.current;
    if (!dialog) return;
    const dialogElement = dialog;

    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab") return;

      const focusableElements = Array.from(
        dialogElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
      ).filter((element) => element.tabIndex >= 0 && element.getAttribute("aria-hidden") !== "true");

      if (focusableElements.length === 0) {
        event.preventDefault();
        dialogElement.focus();
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      const activeElement = document.activeElement;

      if (event.shiftKey && (activeElement === firstElement || !dialogElement.contains(activeElement))) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && (activeElement === lastElement || !dialogElement.contains(activeElement))) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      if (returnFocusElement?.isConnected) returnFocusElement.focus();
    };
  }, [onClose, returnFocusRef]);

  return (
    <div className="journal-overlay" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section
        ref={dialogRef}
        className="learning-journal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="journal-title"
        aria-describedby="journal-description"
        tabIndex={-1}
      >
        <div className="journal-header">
          <div>
            <p>LEARNING CONSTELLATION</p>
            <h2 id="journal-title">星光手记</h2>
            <span id="journal-description">每一颗亮起的星，都是你认真思考过的一天。</span>
          </div>
          <button ref={closeButtonRef} type="button" aria-label="关闭星光手记" onClick={onClose}>×</button>
        </div>
        {isLoading && <p className="journal-state" role="status">正在翻开星光手记…</p>}
        {error && <p className="inline-error" role="alert">{error}</p>}
        {!isLoading && !error && entries.length === 0 && (
          <p className="journal-state">这里还没有手记。点亮今天的第一颗星，故事就开始了。</p>
        )}
        {!isLoading && !error && entries.length > 0 && (
          <ol className="journal-list">
            {entries.map((entry) => (
              <li key={`${entry.local_date}-${entry.task_key}`}>
                <div className="journal-date">
                  <span aria-hidden="true">✦</span>
                  <time dateTime={entry.local_date}>{displayDate(entry.local_date)}</time>
                </div>
                <div>
                  <div className="journal-title-row">
                    <h3>{entry.task_title}</h3>
                    <span>{entry.was_correct ? "猜想与答案一致" : "从不同猜想中发现"}</span>
                  </div>
                  <blockquote>“{entry.reflection}”</blockquote>
                </div>
              </li>
            ))}
          </ol>
        )}
        <button className="secondary-button journal-close" type="button" onClick={onClose}>返回我的星图</button>
      </section>
    </div>
  );
}
