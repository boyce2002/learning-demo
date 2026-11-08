import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  fetchHistory,
  fetchProgress,
  fetchToday,
  resetDemo,
  submitAttempt,
  submitCompletion,
} from "./api/client";
import { AppShell } from "./components/AppShell";
import { ChallengeCard } from "./components/ChallengeCard";
import { CompletionStep } from "./components/CompletionStep";
import { DailyHeader } from "./components/DailyHeader";
import { DemoToolbar } from "./components/DemoToolbar";
import { GuessStep } from "./components/GuessStep";
import { LearningJournal } from "./components/LearningJournal";
import { ProgressPanel } from "./components/ProgressPanel";
import { ReflectionStep } from "./components/ReflectionStep";
import { RevealStep } from "./components/RevealStep";
import { ErrorState, LoadingState } from "./components/SystemState";
import type { DashboardData, HistoryEntry, UiStep } from "./types";

type LoadStatus = "loading" | "ready" | "error";

function stepForPhase(phase: DashboardData["today"]["phase"]): UiStep {
  if (phase === "attempted") return "reveal";
  if (phase === "completed") return "complete";
  return "home";
}

function messageFrom(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export default function App() {
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [step, setStep] = useState<UiStep>("home");
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [reflection, setReflection] = useState("");
  const [loadError, setLoadError] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [freshCompletion, setFreshCompletion] = useState(false);
  const [demoDate, setDemoDate] = useState("");
  const [demoBaseDate, setDemoBaseDate] = useState("");
  const [showJournal, setShowJournal] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const requestSequence = useRef(0);
  const activeRequest = useRef<AbortController | null>(null);
  const historyRequestSequence = useRef(0);
  const activeHistoryRequest = useRef<AbortController | null>(null);
  const journalButtonRef = useRef<HTMLButtonElement>(null);

  const closeJournal = useCallback(() => {
    activeHistoryRequest.current?.abort();
    activeHistoryRequest.current = null;
    historyRequestSequence.current += 1;
    setShowJournal(false);
    setHistoryLoading(false);
    setHistoryError(null);
  }, []);

  const loadDashboard = useCallback(async (requestedDemoDate?: string) => {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    const requestId = ++requestSequence.current;
    setStatus("loading");
    setLoadError("");
    try {
      // The first response establishes the signed anonymous session cookie.
      // Keep the initial calls ordered so two cookie-less requests cannot race
      // and receive different visitor identities.
      const today = await fetchToday(controller.signal, requestedDemoDate);
      const progress = await fetchProgress(controller.signal, requestedDemoDate);
      if (requestId !== requestSequence.current) return;
      if (today.reference_date !== progress.reference_date) {
        throw new ApiError("星图日期没有对齐，请重新连接。", "DATE_MISMATCH");
      }
      setDashboard({ today, progress });
      setStep(stepForPhase(today.phase));
      setSelectedOption(today.attempt?.selected_option ?? null);
      setReflection(today.completion?.reflection ?? "");
      setFreshCompletion(false);
      setDemoDate(today.reference_date);
      setDemoBaseDate((current) => current || today.reference_date);
      setSubmitError(null);
      setStatus("ready");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      if (requestId !== requestSequence.current) return;
      setLoadError(messageFrom(error, "星图暂时没连上，请再试一次。"));
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
    return () => {
      activeRequest.current?.abort();
      activeHistoryRequest.current?.abort();
      historyRequestSequence.current += 1;
    };
  }, [loadDashboard]);

  async function onReveal() {
    if (!dashboard || !selectedOption || isSubmitting) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const attempt = await submitAttempt(
        dashboard.today.task.key,
        selectedOption,
        dashboard.today.is_demo_mode ? demoDate : undefined,
      );
      setDashboard((current) => current && ({
        ...current,
        today: { ...current.today, phase: "attempted", attempt },
      }));
      setStep("reveal");
    } catch (error) {
      if (error instanceof ApiError && ["ATTEMPT_LOCKED", "TASK_MISMATCH"].includes(error.code || "")) {
        await loadDashboard(dashboard.today.is_demo_mode ? demoDate : undefined);
      } else {
        setSubmitError(messageFrom(error, "这次没能揭晓，保留了你的选择。请再试一次。"));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onComplete() {
    if (!dashboard || isSubmitting) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const result = await submitCompletion(
        dashboard.today.task.key,
        reflection,
        dashboard.today.is_demo_mode ? demoDate : undefined,
      );
      setDashboard((current) => current && ({
        today: {
          ...current.today,
          phase: "completed",
          completion: result.completion,
        },
        progress: result.progress,
      }));
      setReflection(result.completion.reflection);
      setFreshCompletion(result.newly_completed);
      setStep("complete");
    } catch (error) {
      setSubmitError(messageFrom(error, "星光暂时没存好，你的话还在这里。请再试一次。"));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onResetDemo() {
    if (!window.confirm("确定清空当前匿名访客的完成与猜想记录吗？此操作不可撤销。")) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await resetDemo();
      closeJournal();
      await loadDashboard(demoDate);
    } catch (error) {
      setSubmitError(messageFrom(error, "演示记录暂时没能重置，请稍后再试。"));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function openJournal() {
    if (!dashboard) return;
    activeHistoryRequest.current?.abort();
    const controller = new AbortController();
    activeHistoryRequest.current = controller;
    const requestId = ++historyRequestSequence.current;
    setShowJournal(true);
    setHistory([]);
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const entries = await fetchHistory(
        7,
        dashboard.today.is_demo_mode ? demoDate : undefined,
        controller.signal,
      );
      if (requestId !== historyRequestSequence.current) return;
      setHistory(entries);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      if (requestId !== historyRequestSequence.current) return;
      setHistoryError(messageFrom(error, "星光手记暂时没有打开，请再试一次。"));
    } finally {
      if (requestId === historyRequestSequence.current) {
        if (activeHistoryRequest.current === controller) activeHistoryRequest.current = null;
        setHistoryLoading(false);
      }
    }
  }

  if (status === "loading") {
    return <AppShell><LoadingState /></AppShell>;
  }
  if (status === "error" || !dashboard) {
    return <AppShell><ErrorState message={loadError} onRetry={() => void loadDashboard(demoDate || undefined)} /></AppShell>;
  }

  const { today, progress } = dashboard;
  let mainCard;
  if (step === "guess") {
    mainCard = (
      <GuessStep
        task={today.task}
        selectedOption={selectedOption}
        isSubmitting={isSubmitting}
        error={submitError}
        onSelect={(option) => { setSelectedOption(option); setSubmitError(null); }}
        onReveal={() => void onReveal()}
      />
    );
  } else if (step === "reveal" && today.attempt) {
    mainCard = <RevealStep task={today.task} attempt={today.attempt} onReflect={() => setStep("reflect")} />;
  } else if (step === "reflect" && today.attempt) {
    mainCard = (
      <ReflectionStep
        prompt={today.attempt.reflection_prompt}
        value={reflection}
        isSubmitting={isSubmitting}
        error={submitError}
        onChange={(value) => { setReflection(value); setSubmitError(null); }}
        onBack={() => setStep("reveal")}
        onComplete={() => void onComplete()}
      />
    );
  } else if (step === "complete" && today.completion) {
    mainCard = (
      <CompletionStep
        completion={today.completion}
        progress={progress}
        animate={freshCompletion}
        onHome={() => { setFreshCompletion(false); setStep("home"); }}
        onReview={() => { setFreshCompletion(false); setStep("reveal"); }}
      />
    );
  } else {
    mainCard = (
      <ChallengeCard
        task={today.task}
        completed={today.phase === "completed"}
        onStart={() => setStep(today.phase === "completed" ? "complete" : "guess")}
      />
    );
  }

  return (
    <AppShell isDemoMode={today.is_demo_mode}>
      <DailyHeader referenceDate={today.reference_date} />
      {today.is_demo_mode && demoBaseDate && (
        <DemoToolbar
          baseDate={demoBaseDate}
          selectedDate={demoDate}
          canReset={today.demo_reset_enabled}
          isBusy={isSubmitting}
          onDateChange={(date) => { closeJournal(); void loadDashboard(date); }}
          onReset={() => void onResetDemo()}
        />
      )}
      {submitError && step === "home" && <p className="page-error inline-error" role="alert">{submitError}</p>}
      <main id="main-content" className="dashboard-grid">
        {mainCard}
        <ProgressPanel
          progress={progress}
          onOpenJournal={() => void openJournal()}
          journalButtonRef={journalButtonRef}
        />
      </main>
      {showJournal && (
        <LearningJournal
          entries={history}
          isLoading={historyLoading}
          error={historyError}
          onClose={closeJournal}
          returnFocusRef={journalButtonRef}
        />
      )}
    </AppShell>
  );
}
