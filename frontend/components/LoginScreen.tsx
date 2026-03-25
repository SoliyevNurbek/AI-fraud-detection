"use client";

import { FormEvent, useState } from "react";
import styles from "@/components/dashboard.module.css";

type Props = {
  onLogin: (username: string, password: string) => Promise<void>;
};

export function LoginScreen({ onLogin }: Props) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await onLogin(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <main className={styles.loginShell}>
      <section className={styles.loginGrid}>
        <div className={`${styles.panel} ${styles.heroPanel} ${styles.loginIntro}`}>
          <span className={styles.eyebrow}>SentraShield X</span>
          <h1 className={styles.heading}>Analyst Access</h1>
          <p className={styles.subcopy}>
            Sign in to the fraud command center. Default local credentials are prefilled for development.
          </p>
          <div className={styles.heroList}>
            <div className={styles.heroListItem}>
              <span className={styles.muted}>Realtime pipeline</span>
              <strong>REST + WebSocket + AI scoring</strong>
            </div>
            <div className={styles.heroListItem}>
              <span className={styles.muted}>Local demo</span>
              <strong>admin / admin123</strong>
            </div>
            <div className={styles.heroListItem}>
              <span className={styles.muted}>Best for</span>
              <strong>Fraud ops, review queue, live triage</strong>
            </div>
          </div>
        </div>

        <section className={`${styles.panel} ${styles.loginCard}`}>
          <h2>Secure Sign-In</h2>
          <p className={styles.subcopy}>JWT auth against the FastAPI backend on port 8000.</p>
          <form onSubmit={handleSubmit} className={styles.formGrid}>
            <label className={styles.field}>
              <span className={styles.muted}>Username</span>
              <input className={styles.input} value={username} onChange={(e) => setUsername(e.target.value)} />
            </label>
            <label className={styles.field}>
              <span className={styles.muted}>Password</span>
              <input className={styles.input} type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </label>
            <div className={styles.actionRow} style={{ gridColumn: "1 / -1" }}>
              <div className={styles.muted}>{error ?? "Local analyst account is ready for development use."}</div>
              <button className={styles.button} disabled={pending} type="submit">
                {pending ? "Signing in..." : "Open Dashboard"}
              </button>
            </div>
          </form>
        </section>
      </section>
    </main>
  );
}