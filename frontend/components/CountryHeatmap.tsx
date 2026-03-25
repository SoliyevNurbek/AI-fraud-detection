import styles from "@/components/dashboard.module.css";
import type { CountryPoint } from "@/lib/types";

export function CountryHeatmap({ countries }: { countries: CountryPoint[] }) {
  return (
    <div className={styles.countryGrid}>
      {countries.length === 0 ? (
        <div className={styles.countryCard}>
          <div className={styles.muted}>No country telemetry yet. Trigger a few transactions to populate this panel.</div>
        </div>
      ) : null}
      {countries.map((country) => (
        <div className={styles.countryCard} key={country.country_code}>
          <div className={styles.countryTop}>
            <strong>{country.country_code}</strong>
            <span className={styles.muted}>{country.count} tx</span>
          </div>
          <div className={styles.heatTrack}>
            <div className={styles.heatFill} style={{ width: `${country.avg_risk}%` }} />
          </div>
          <div className={styles.heroListItem} style={{ marginTop: 12, padding: 0, background: "transparent", border: 0 }}>
            <span className={styles.muted}>Average risk</span>
            <strong>{country.avg_risk.toFixed(2)}</strong>
          </div>
        </div>
      ))}
    </div>
  );
}
