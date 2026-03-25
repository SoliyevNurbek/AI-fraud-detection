import styles from "@/components/dashboard.module.css";
import type { TrendPoint } from "@/lib/types";

export function TrendChart({ points }: { points: TrendPoint[] }) {
  const peak = Math.max(...points.map((point) => point.value), 1);

  return (
    <div className={styles.barGrid}>
      {points.map((point) => (
        <div className={styles.barCol} key={point.label}>
          <div className={styles.barValue}>{point.value}</div>
          <div className={styles.bar} style={{ height: `${Math.max((point.value / peak) * 220, 18)}px` }} />
          <div className={styles.barLabel}>{point.label.replace("_", " ")}</div>
        </div>
      ))}
    </div>
  );
}