"use client";

import { FormEvent, useState } from "react";
import styles from "@/components/dashboard.module.css";
import type { ScoreResponse } from "@/lib/types";

const initialState = {
  external_txn_id: `txn-${Date.now()}`,
  user_id: "demo-user-1",
  device_fingerprint: "demo-device-x",
  amount: "9000",
  currency: "USD",
  merchant_category: "crypto",
  ip_address: "185.23.1.10",
  country_code: "RU",
};

type Props = {
  onSubmit: (payload: Record<string, unknown>) => Promise<ScoreResponse>;
};

export function TransactionSimulator({ onSubmit }: Props) {
  const [form, setForm] = useState(initialState);
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSentAt, setLastSentAt] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const payload = {
        ...form,
        amount: Number(form.amount),
        event_time: new Date().toISOString(),
      };
      const response = await onSubmit(payload);
      setResult(response);
      setLastSentAt(new Date().toLocaleTimeString());
      setForm((current) => ({ ...current, external_txn_id: `txn-${Date.now()}` }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className={styles.panel}>
      <h2>Transaction Simulator</h2>
      <p className={styles.subcopy}>Fire webhook traffic directly from the dashboard to test AI + rules + alert broadcast.</p>
      <div className={styles.simulatorBanner}>
        <span className={styles.muted}>Webhook target</span>
        <strong>POST /webhook/transaction</strong>
        <span className={styles.muted}>{lastSentAt ? `Last sent at ${lastSentAt}` : "Ready to submit a live test transaction"}</span>
      </div>
      <form className={styles.formGrid} onSubmit={handleSubmit}>
        {Object.entries(form).map(([key, value]) => (
          <label className={styles.field} key={key}>
            <span className={styles.muted}>{key}</span>
            {key === "merchant_category" || key === "country_code" ? (
              <select className={styles.select} value={value} onChange={(e) => setForm((current) => ({ ...current, [key]: e.target.value }))}>
                {key === "merchant_category" ? (
                  <>
                    <option value="crypto">crypto</option>
                    <option value="electronics">electronics</option>
                    <option value="gaming">gaming</option>
                    <option value="retail">retail</option>
                  </>
                ) : (
                  <>
                    <option value="RU">RU</option>
                    <option value="US">US</option>
                    <option value="GB">GB</option>
                    <option value="SY">SY</option>
                  </>
                )}
              </select>
            ) : (
              <input className={styles.input} value={value} onChange={(e) => setForm((current) => ({ ...current, [key]: e.target.value }))} />
            )}
          </label>
        ))}
        <div className={styles.actionRow} style={{ gridColumn: "1 / -1" }}>
          <div className={styles.muted}>{error ?? "Posts to /webhook/transaction"}</div>
          <button className={styles.button} disabled={pending} type="submit">
            {pending ? "Scoring..." : "Run Transaction"}
          </button>
        </div>
      </form>

      {result ? (
        <div className={styles.statusCard}>
          <strong>{result.status.toUpperCase()}</strong>
          <div className={styles.heroList}>
            <div className={styles.heroListItem}>
              <span className={styles.muted}>Decision</span>
              <strong>{result.decision}</strong>
            </div>
            <div className={styles.heroListItem}>
              <span className={styles.muted}>Risk score</span>
              <strong>{result.risk_score.toFixed(2)}</strong>
            </div>
            <div className={styles.heroListItem}>
              <span className={styles.muted}>Transaction ID</span>
              <strong>{result.transaction_id.slice(0, 12)}</strong>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}