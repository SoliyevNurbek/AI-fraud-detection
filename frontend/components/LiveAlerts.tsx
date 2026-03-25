import styles from "@/components/dashboard.module.css";
import type { AlertItem } from "@/lib/types";

function severityClass(severity: string) {
  if (severity === "critical") return styles.critical;
  if (severity === "high") return styles.high;
  if (severity === "medium") return styles.medium;
  return styles.low;
}

export function LiveAlerts({ alerts }: { alerts: AlertItem[] }) {
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Severity</th>
            <th>Status</th>
            <th>Title</th>
            <th>Reason</th>
            <th>Risk</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {alerts.length === 0 ? (
            <tr>
              <td className={styles.muted} colSpan={7}>
                No alerts yet. Use the transaction simulator to create live cases.
              </td>
            </tr>
          ) : null}
          {alerts.map((alert) => (
            <tr key={alert.id ?? alert.alert_id ?? `${alert.title}-${alert.created_at}`}>
              <td>{(alert.id ?? alert.alert_id ?? "").slice(0, 8)}</td>
              <td>
                <span className={`${styles.chip} ${severityClass(alert.severity)}`}>{alert.severity}</span>
              </td>
              <td>{alert.status}</td>
              <td>{alert.title}</td>
              <td className={styles.muted}>{alert.description}</td>
              <td>{alert.risk_score.toFixed(2)}</td>
              <td className={styles.muted}>{new Date(alert.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}