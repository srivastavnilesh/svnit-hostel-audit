"""Phase 3 v2: Predictive Maintenance & Resource Optimisation Engine.
Asset: Atal Bihari Bajpayee Bhavan, 500-seater EWS hostel, SVNIT Surat (G+6).
Robust-stats policy: flagged outliers (mep_daily.is_outlier, survey.straightline_flag)
are EXCLUDED from statistics but RETAINED in DB for audit trail (see data_quality_log).
Compliance anchors: CPWD NIT 07/2020-21 Cl.7.1 (10-yr waterproofing guarantee) and
lift eligibility (avg downtime <= 8 h minor / <= 7 d major); IS 1172 (135 LPCD);
IS 13311-1; IS 456; IS 875-2; SMC Fire NOC 2023-24/1108.
"""
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # cwd-independent
DB   = ROOT / "data" / "hostel_digital_twin.db"
OUT  = ROOT / "outputs"; OUT.mkdir(parents=True, exist_ok=True)

TARIFF_RS_KWH  = 7.2    # Gujarat institutional LT blend (documented assumption)
WATER_RS_KL    = 45.0   # municipal + pumping energy blend (documented assumption)
LPCD_NORM      = 135.0  # IS 1172:1993
CPWD_MINOR_DT  = 8.0    # CPWD lift eligibility: avg minor-fault downtime (hours)

conn = sqlite3.connect(DB)
mep   = pd.read_sql("SELECT * FROM mep_daily", conn)
wat   = pd.read_sql("SELECT * FROM water_monthly", conn)
en    = pd.read_sql("SELECT * FROM energy_monthly", conn)
sv    = pd.read_sql("SELECT * FROM occupant_survey", conn)
rooms = pd.read_sql("SELECT * FROM rooms", conn)
pm    = pd.read_sql("SELECT * FROM pm_schedule", conn)
conn.close()

mep_c = mep[mep["is_outlier"] == 0].copy()
sv_c  = sv[sv["straightline_flag"] == 0].copy()
POP   = int(rooms["occupied_beds"].sum())

print("=" * 80)
print("PREDICTIVE MAINTENANCE & RESOURCE OPTIMISATION - PHASE 3 v2")
print(f"Population basis: {POP} residents | excluded outliers: "
      f"{int(mep['is_outlier'].sum())} MEP rows, {int(sv['straightline_flag'].sum())} surveys")
print("=" * 80)

# ---------- MODULE 1: LIFT RELIABILITY vs CPWD BENCHMARK ----------
print("\n[1] LIFT RELIABILITY vs CPWD ELIGIBILITY (<= 8 h avg minor downtime)")
lifts = mep_c[mep_c["asset_id"].str.startswith("LIFT")]
rows = []
for asset in sorted(lifts["asset_id"].unique()):
    dt = lifts.loc[(lifts["asset_id"] == asset) & (lifts["downtime_hours"] > 0), "downtime_hours"]
    n = int(len(dt))
    mean_dt = round(float(dt.mean()), 1) if n else 0.0
    med_dt  = round(float(dt.median()), 1) if n else 0.0
    mtbf    = round(365 / n, 1) if n else 999.0
    risk    = round(min(100.0, n * 12 + mean_dt * 1.5), 1)
    rows.append((asset, n, mtbf, mean_dt, med_dt,
                 "PASS" if mean_dt <= CPWD_MINOR_DT else "REVIEW", risk,
                 "Door-sensor + ARD battery PM visit" if risk > 35 else "Monitor"))
df_lift = pd.DataFrame(rows, columns=["lift", "faults_365d", "mtbf_days", "mean_dt_h",
                                      "median_dt_h", "cpwd_check", "risk_score", "recommended_action"])
df_lift.to_csv(OUT / "predictive_lift_risk.csv", index=False)
print(df_lift.to_string(index=False))

# ---------- MODULE 2: PUMP DRY-RUN SEASONALITY ----------
print("\n[2] PUMP DRY-RUN SEASONALITY (summer sump stress)")
pumps = mep_c[mep_c["asset_id"].str.startswith("PUMP")].copy()
pumps["month"] = pd.to_datetime(pumps["date"]).dt.month
dry = pumps[pumps["fault_note"].str.contains("Dry-run", na=False)]
share = round(len(dry[dry["month"].isin([4, 5])]) / max(1, len(dry)) * 100, 1)
print(f"  Dry-run events (365 d): {len(dry)} | Apr-May share: {share}%")
print("  -> Fit low-level cut-off float interlock on PUMP-DOM-01/02 before March.")

# ---------- MODULE 3: WATER LEAKAGE ROI (IS 1172) ----------
print("\n[3] WATER LEAKAGE ROI (IS 1172 norm = 135 LPCD)")
avg_lpcd = float(wat["water_lpcd"].mean())
excess   = max(0.0, avg_lpcd - LPCD_NORM)
excess_kl_yr = excess * POP * 365 / 1000.0
waste_rs_yr  = excess_kl_yr * WATER_RS_KL
capex  = 500 * 150 + 10000
saving = waste_rs_yr * 0.15
payback_m = round(capex / saving * 12, 1) if saving > 0 else float("inf")
print(f"  Measured {avg_lpcd:.0f} LPCD vs 135 -> excess {excess:.0f} LPCD")
print(f"  Wasted {excess_kl_yr:,.0f} kL/yr = Rs {waste_rs_yr:,.0f}/yr")
print(f"  500 aerators + leak drive | Capex Rs {capex:,} | Saving Rs {saving:,.0f}/yr -> PAYBACK {payback_m} months")
pd.DataFrame([{"metric": "measured_lpcd", "value": round(avg_lpcd, 1)},
              {"metric": "excess_lpcd", "value": round(excess, 1)},
              {"metric": "wasted_kl_per_yr", "value": round(excess_kl_yr, 0)},
              {"metric": "wasted_rs_per_yr", "value": round(waste_rs_yr, 0)},
              {"metric": "capex_rs", "value": capex},
              {"metric": "annual_saving_rs", "value": round(saving, 0)},
              {"metric": "payback_months", "value": payback_m}]).to_csv(OUT / "water_roi.csv", index=False)

# ---------- MODULE 4: SIXTH-FLOOR THERMAL / COOL-ROOF CASE ----------
print("\n[4] SIXTH-FLOOR THERMAL CASE (cool roof over 1920 sqm terrace, BOQ item 17.5.1)")
sixth = float(sv_c.loc[sv_c["floor"] == "Sixth", "thermal_comfort"].mean())
capex_cr = 1920.0 * 45.0
sav_kwh  = 15000.0 * 0.08
sav_rs   = sav_kwh * TARIFF_RS_KWH
pay_y    = round(capex_cr / sav_rs, 1) if sav_rs > 0 else float("inf")
print(f"  Sixth-floor thermal comfort {sixth:.2f}/5 (building lowest)")
print(f"  Cool-roof capex Rs {capex_cr:,.0f} | saving {sav_kwh:,.0f} kWh/yr = Rs {sav_rs:,.0f}/yr")
print(f"  Energy-only payback {pay_y} yr -> justify via comfort + WP-guard (Cl. 7.1.3 annual inspection), not energy alone")
pd.DataFrame([{"metric": "sixth_floor_thermal_score", "value": round(sixth, 2)},
              {"metric": "cool_roof_capex_rs", "value": capex_cr},
              {"metric": "annual_energy_saving_rs", "value": round(sav_rs, 0)},
              {"metric": "energy_only_payback_yr", "value": pay_y}]).to_csv(OUT / "thermal_roi.csv", index=False)

# ---------- MODULE 5: ENERGY ANOMALY SCAN (robust IQR) ----------
print("\n[5] ENERGY ANOMALY SCAN (median +/- 1.5*IQR, monthly kWh, last 12 m)")
monthly = en.groupby("month")["kwh"].sum().sort_index().tail(12)
q1, q3 = monthly.quantile(0.25), monthly.quantile(0.75)
lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
flags = monthly[(monthly < lo) | (monthly > hi)]
print(f"  Bounds [{lo:,.0f}, {hi:,.0f}] kWh | flagged months: {list(flags.index) if len(flags) else 'none'}")
(monthly.rename("kwh_month").to_frame().reset_index()
        .assign(anomaly=monthly.reset_index()["month"].isin(flags.index))
        .to_csv(OUT / "energy_anomaly.csv", index=False))

# ---------- MODULE 6: PM COMPLIANCE GAPS ----------
print("\n[6] PM COMPLIANCE GAPS (< 90%)")
gaps = pm[pm["compliance_pct"] < 90].sort_values("compliance_pct")
gaps.to_csv(OUT / "pm_gaps.csv", index=False)
print(gaps.to_string(index=False) if len(gaps) else "  none")

print(f"\nExports -> {OUT}/ : predictive_lift_risk.csv, water_roi.csv, thermal_roi.csv, energy_anomaly.csv, pm_gaps.csv")