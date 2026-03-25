"use client";

import { useEffect, useState } from "react";
import styles from "@/components/dashboard.module.css";
import { CountryHeatmap } from "@/components/CountryHeatmap";
import { LiveAlerts } from "@/components/LiveAlerts";
import { LoginScreen } from "@/components/LoginScreen";
import { TransactionSimulator } from "@/components/TransactionSimulator";
import { TrendChart } from "@/components/TrendChart";
import { fetchAlerts, fetchSummary, getApiBaseUrl, getWsAlertsUrl, login, simulateTransaction } from "@/lib/api";
import type { AlertItem, ConnectionState, DashboardSummary } from "@/lib/types";

const tokenStorageKey = "sentrashield_token";

export function DashboardClient() {
  const [token, setToken] = useState<string | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [status, setStatus] = useState<ConnectionState>("Connecting");
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(tokenStorageKey);
    if (stored) {
      setToken(stored);
    }
  }, []);

  useEffect(() => {
    if (!token) return;

    const authToken = token;
    let active = true;
    let socket: WebSocket | null = null;

    async function load(showSyncState = false) {
      try {
        if (showSyncState) {
          setRefreshing(true);
          setStatus("Syncing");
        }

        const [nextSummary, nextAlerts] = await Promise.all([fetchSummary(authToken), fetchAlerts(authToken)]);
        if (!active) return;
        setSummary(nextSummary);
        setAlerts(nextAlerts);
        setError(null);
        setStatus("Live");
      } catch (err) {
        if (!active) return;
        const message = err instanceof Error ? err.message : "Failed to load dashboard";
        setError(message);
        setStatus("Disconnected");
        if (message.toLowerCase().includes("invalid token") || message.toLowerCase().includes("missing bearer token")) {
          window.localStorage.removeItem(tokenStorageKey);
          setToken(null);
        }
      } finally {
        if (active) {
          setRefreshing(false);
        }
      }
    }

    void load(true);

    try {
      socket = new WebSocket(getWsAlertsUrl());
    } catch {
      setStatus("Stream error");
    }

    if (!socket) {
      return () => {
        active = false;
      };
    }

    socket.onopen = () => {
      setStatus("Live");
      socket?.send("ping");
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as AlertItem | { type: string };
        if ("type" in payload) return;
        setAlerts((current) => [payload, ...current].slice(0, 12));
        void load();
      } catch {
        setStatus("Stream issue");
      }
    };

    socket.onclose = () => {
      if (active) {
        setStatus("Disconnected");
      }
    };

    socket.onerror = () => setStatus("Stream error");

    return () => {
      active = false;
      socket?.close();
    };
  }, [token]);

  async function handleLogin(username: string, password: string) {
    const response = await login(username, password);
    window.localStorage.setItem(tokenStorageKey, response.access_token);
    setToken(response.access_token);
    setError(null);
  }

  async function handleSimulate(payload: Record<string, unknown>) {
    const response = await simulateTransaction(payload);
    if (token) {
      const authToken = token;
      const [nextSummary, nextAlerts] = await Promise.all([fetchSummary(authToken), fetchAlerts(authToken)]);
      setSummary(nextSummary);
      setAlerts(nextAlerts);
      setStatus("Live");
    }
    return response;
  }

  function handleLogout() {
    window.localStorage.removeItem(tokenStorageKey);
    setToken(null);
    setSummary(null);
    setAlerts([]);
    setError(null);
    setStatus("Connecting");
  }

  if (!token) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <section className={styles.hero}>
          <div className={`${styles.panel} ${styles.heroPanel}`}>
            <div className={styles.heroTopRow}>
              <span className={styles.eyebrow}>SentraShield X</span>
              <button className={`${styles.button} ${styles.buttonSecondary}`} onClick={handleLogout} type="button">
                Logout
              </button>
            </div>
            <h1 className={styles.heading}>Fraud Command Center</h1>
            <p className={styles.subcopy}>
              Live fintech screening workspace backed by FastAPI, AI inference, alert scoring, and websocket push. API base:{" "}
              <span className={styles.inlineCode}>{getApiBaseUrl()}</span>
            </p>
            <div className={styles.signalStrip}>
              <div className={styles.signalCard}>
                <span className={styles.muted}>Sync state</span>
                <strong>{refreshing ? "Refreshing data" : status}</strong>
              </div>
              <div className={styles.signalCard}>
                <span className={styles.muted}>Alert stream</span>
                <strong>{alerts.length} recent items</strong>
              </div>
            </div>
            <div className={styles.heroList}>
              <div className={styles.heroListItem}>
                <span className={styles.muted}>Realtime stream</span>
                <strong>{status}</strong>
              </div>
              <div className={styles.heroListItem}>
                <span className={styles.muted}>Model version</span>
                <strong>{summary?.model_version ?? "loading"}</strong>
              </div>
              <div className={styles.heroListItem}>
                <span className={styles.muted}>Average risk</span>
                <strong>{summary?.average_risk?.toFixed(2) ?? "--"}</strong>
              </div>
            </div>
            {summary ? <TrendChart points={summary.trend} /> : null}
          </div>

          <div className={`${styles.panel} ${styles.sidePanel}`}>
            <h2>System Flow</h2>
            <div className={styles.heroList}>
              <div className={styles.heroListItem}><span className={styles.muted}>1. Intake</span><strong>Webhook / REST / Auth</strong></div>
              <div className={styles.heroListItem}><span className={styles.muted}>2. Features</span><strong>Amount, device, IP, country, velocity</strong></div>
              <div className={styles.heroListItem}><span className={styles.muted}>3. AI</span><strong>XGBoost-ready fallback inference</strong></div>
              <div className={styles.heroListItem}><span className={styles.muted}>4. Ops</span><strong>Alert queue, heatmap, analyst review</strong></div>
            </div>
            <div className={styles.sideNote}>
              <span className={styles.muted}>Runtime note</span>
              <strong>{error ?? "Frontend and backend are connected."}</strong>
            </div>
          </div>
        </section>

        <section className={styles.kpiGrid}>
          {[
            ["Transactions", summary?.transactions ?? 0],
            ["Alerts", summary?.alerts ?? 0],
            ["High Risk", summary?.high_risk ?? 0],
            ["Blocked", summary?.blocked ?? 0],
            ["Review Queue", summary?.recent_reviews ?? 0],
          ].map(([label, value]) => (
            <div className={`${styles.panel} ${styles.kpiCard}`} key={label}>
              <div className={styles.kpiLabel}>{label}</div>
              <div className={styles.kpiValue}>{value}</div>
            </div>
          ))}
        </section>

        <section className={styles.contentGrid}>
          <div className={styles.stack}>
            <section className={styles.panel}>
              <h2>Live Investigation Queue</h2>
              <p className={styles.subcopy}>Fresh alerts appear here as the backend broadcasts new fraud cases.</p>
              <LiveAlerts alerts={alerts} />
            </section>
            <TransactionSimulator onSubmit={handleSimulate} />
          </div>

          <div className={styles.stack}>
            <section className={styles.panel}>
              <h2>Country Risk Heatmap</h2>
              <p className={styles.subcopy}>Risk concentration across recent scored transactions.</p>
              <CountryHeatmap countries={summary?.countries ?? []} />
            </section>
            <section className={styles.panel}>
              <h2>Operator Notes</h2>
              <div className={styles.heroList}>
                <div className={styles.heroListItem}>
                  <span className={styles.muted}>Auth</span>
                  <strong>JWT bearer session</strong>
                </div>
                <div className={styles.heroListItem}>
                  <span className={styles.muted}>Detection</span>
                  <strong>Rules + ML blend</strong>
                </div>
                <div className={styles.heroListItem}>
                  <span className={styles.muted}>Realtime</span>
                  <strong>FastAPI websocket alerts</strong>
                </div>
                <div className={styles.heroListItem}>
                  <span className={styles.muted}>Issue</span>
                  <strong>{error ?? "No active errors"}</strong>
                </div>
              </div>
            </section>
          </div>
        </section>
      </div>
    </main>
  );
}