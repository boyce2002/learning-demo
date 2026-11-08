export type Phase = "not_started" | "attempted" | "completed";
export type UiStep = "home" | "guess" | "reveal" | "reflect" | "complete";
export type WeekStatus = "done" | "missed" | "today_pending" | "future";

export interface TaskOption {
  key: string;
  label: string;
}

export interface PublicTask {
  key: string;
  category: string;
  title: string;
  question: string;
  estimated_minutes: number;
  options: TaskOption[];
}

export interface AttemptDetail {
  selected_option: string;
  was_correct: boolean;
  correct_option: string;
  feedback: string;
  explanation: string;
  takeaway: string;
  reflection_prompt: string;
}

export interface CompletionDetail {
  reflection: string;
  completed_at_utc: string;
}

export interface TodayResponse {
  reference_date: string;
  timezone: string;
  is_demo_mode: boolean;
  demo_reset_enabled: boolean;
  user_id: "anonymous_visitor";
  phase: Phase;
  task: PublicTask;
  attempt: AttemptDetail | null;
  completion: CompletionDetail | null;
}

export interface WeekDay {
  date: string;
  status: WeekStatus;
}

export interface ProgressResponse {
  reference_date: string;
  streak_days: number;
  total_completed_days: number;
  today_completed: boolean;
  week_days: WeekDay[];
}

export interface CompleteResponse {
  newly_completed: boolean;
  completion: CompletionDetail;
  progress: ProgressResponse;
}

export interface DashboardData {
  today: TodayResponse;
  progress: ProgressResponse;
}

export interface HistoryEntry {
  local_date: string;
  task_key: string;
  task_title: string;
  reflection: string;
  was_correct: boolean;
  completed_at_utc: string;
}
