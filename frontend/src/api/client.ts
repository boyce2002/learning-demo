import type {
  AttemptDetail,
  CompleteResponse,
  HistoryEntry,
  ProgressResponse,
  TodayResponse,
} from "../types";

interface ErrorDetail {
  code?: string;
  message?: string;
}

export class ApiError extends Error {
  code?: string;
  status?: number;

  constructor(message: string, code?: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

function withDemoDate(path: string, demoDate?: string): string {
  if (!demoDate) return path;
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}demo_date=${encodeURIComponent(demoDate)}`;
}

function readableError(payload: unknown, fallback: string): ErrorDetail {
  if (!payload || typeof payload !== "object") return { message: fallback };
  const detail = (payload as { detail?: unknown }).detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const typed = detail as ErrorDetail;
    return { code: typed.code, message: typed.message || fallback };
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    return { message: first.msg || fallback };
  }
  return { message: fallback };
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...init.headers,
      },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError("星图暂时没连上，请检查网络后再试一次。", "NETWORK_ERROR");
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    if (!response.ok) {
      throw new ApiError("服务暂时没有返回可读信息，请稍后再试。", "INVALID_RESPONSE", response.status);
    }
  }

  if (!response.ok) {
    const detail = readableError(payload, "这次请求没有完成，请再试一次。");
    throw new ApiError(detail.message || "请求失败。", detail.code, response.status);
  }
  return payload as T;
}

export function fetchToday(signal?: AbortSignal, demoDate?: string) {
  return apiRequest<TodayResponse>(withDemoDate("/api/today", demoDate), { signal });
}

export function fetchProgress(signal?: AbortSignal, demoDate?: string) {
  return apiRequest<ProgressResponse>(withDemoDate("/api/progress", demoDate), { signal });
}

export function submitAttempt(
  taskKey: string,
  selectedOption: string,
  demoDate?: string,
) {
  return apiRequest<AttemptDetail>(
    withDemoDate(`/api/tasks/${encodeURIComponent(taskKey)}/attempt`, demoDate),
    {
      method: "POST",
      body: JSON.stringify({ selected_option: selectedOption }),
    },
  );
}

export function submitCompletion(
  taskKey: string,
  reflection: string,
  demoDate?: string,
) {
  return apiRequest<CompleteResponse>(
    withDemoDate(`/api/tasks/${encodeURIComponent(taskKey)}/complete`, demoDate),
    {
      method: "POST",
      body: JSON.stringify({ reflection }),
    },
  );
}

export function fetchHistory(
  limit = 7,
  demoDate?: string,
  signal?: AbortSignal,
) {
  return apiRequest<HistoryEntry[]>(
    withDemoDate(`/api/history?limit=${limit}`, demoDate),
    { signal },
  );
}

export function resetDemo() {
  return apiRequest<{ deleted_attempts: number; deleted_completions: number }>(
    "/api/demo/reset",
    { method: "POST" },
  );
}
