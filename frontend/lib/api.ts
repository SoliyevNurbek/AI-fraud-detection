import type { AlertItem, ApiErrorShape, DashboardSummary, LoginResponse, ScoreResponse } from "@/lib/types";

const DEFAULT_HTTP_PORT = "8000";
const DEFAULT_PROTOCOL = "http:";

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}

function resolveOrigin(explicit: string | undefined, ws = false) {
  if (explicit) {
    return trimTrailingSlash(explicit);
  }

  if (typeof window === "undefined") {
    return `${ws ? "ws:" : DEFAULT_PROTOCOL}//127.0.0.1:${DEFAULT_HTTP_PORT}`;
  }

  const protocol = ws ? (window.location.protocol === "https:" ? "wss:" : "ws:") : window.location.protocol;
  const hostname = window.location.hostname || "127.0.0.1";
  return `${protocol}//${hostname}:${DEFAULT_HTTP_PORT}`;
}

export function getApiBaseUrl() {
  return resolveOrigin(process.env.NEXT_PUBLIC_API_BASE_URL);
}

export function getWsAlertsUrl() {
  const wsBaseUrl = resolveOrigin(process.env.NEXT_PUBLIC_WS_BASE_URL, true);
  return `${wsBaseUrl}/ws/alerts`;
}

function parseErrorMessage(raw: string) {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as ApiErrorShape;
    return parsed.detail ?? parsed.message ?? parsed.error ?? raw;
  } catch {
    return raw;
  }
}

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const controller = new AbortController();
  const timeoutId = globalThis.setTimeout(() => controller.abort(), 12000);

  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init.headers ?? {}),
      },
      cache: "no-store",
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(parseErrorMessage(text) ?? `Request failed: ${response.status}`);
    }

    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Backend response timed out. Check that FastAPI is running on port 8000.");
    }

    if (error instanceof TypeError) {
      throw new Error("Backend is unreachable. Verify the FastAPI server and NEXT_PUBLIC_API_BASE_URL.");
    }

    throw error;
  } finally {
    globalThis.clearTimeout(timeoutId);
  }
}

export async function login(username: string, password: string) {
  return request<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function fetchSummary(token: string) {
  return request<DashboardSummary>("/api/v1/dashboard/summary", {}, token);
}

export async function fetchAlerts(token: string) {
  return request<AlertItem[]>("/api/v1/alerts", {}, token);
}

export async function simulateTransaction(payload: Record<string, unknown>) {
  return request<ScoreResponse>("/webhook/transaction", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}