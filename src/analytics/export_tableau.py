"""Phase 5 prep: Tableau-ready extracts for Atal Bihari Bajpayee Bhavan audit.
Tableau Public reads CSVs only, so this module flattens the SQLite twin + audit
CSVs into tidy, display-named extracts under outputs/tableau/.
Robustness: cwd-anchored paths, table-existence guards, cleaned-sample policy
(retest_flag / straightline_flag / is_outlier excluded per data_quality_log)."""
import sqlite3
import shutil
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB   = ROOT / "data" / "hostel_digital_twin.db"
OUT  = ROOT / "outputs"
T    = OUT / "tableau"; T.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB)
tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
def q(sql): return pd.read_sql(sql, conn)
manifest = {}

# ---------- 1. Structural health by floor (IS 13311-1 / IS 456 flags) ----------
if "structural_ndt" in tables:
    ndt = q("SELECT * FROM structural_ndt WHERE retest_flag = 0")
    ndt["Crack_flag"]    = (ndt["crack_width_mm"] > 0.2).astype(int)     # IS 456 moderate exposure
    ndt["Strength_flag"] = (ndt["rebound_mpa"] < 25).astype(int)         # vs M25 fck
    ndt["Carbon_flag"]   = (ndt["carbonation_mm"] > 12.5).astype(int)    # cover/2 monitor zone
    flr = ndt.groupby("floor").agg(Elements=("tag", "count"), UPV_mean=("upv_km_s", "mean"),
                                   UPV_min=("upv_km_s", "min"), Cracks=("Crack_flag", "sum"),
                                   Damp_patches=("damp_patch", "sum"),
                                   Strength_flags=("Strength_flag", "sum"),
                                   Carbon_flags=("Carbon_flag", "sum")).reset_index()
    flr[["UPV_mean", "UPV_min"]] = flr[["UPV_mean", "UPV_min"]].round(2)
    order = ["Terrace", "Sixth", "Fifth", "Fourth", "Third", "Second", "First", "Ground"]
    flr = flr.assign(sort=flr["floor"].map({f: i for i, f in enumerate(order)})) \
             .sort_values("sort").drop(columns="sort")
    flr.to_csv(T / "floor_structural.csv", index=False); manifest["floor_structural.csv"] = len(flr)

# ---------- 2. Fire NOC 42-condition scorecard ----------
if "fire_noc_conditions" in tables:
    noc = q("SELECT * FROM fire_noc_conditions")
    noc["Status"] = noc["compliance_score"].map(
        lambda s: "Compliant" if s == 100 else ("Partial" if s >= 70 else "Fail"))
    noc.to_csv(T / "noc_conditions.csv", index=False); manifest["noc_conditions.csv"] = len(noc)

# ---------- 3. Lift fleet: traffic engineering + reliability joined ----------
lt_p, lr_p = OUT / "audit_lift_traffic.csv", OUT / "predictive_lift_risk.csv"
if lt_p.exists() and lr_p.exists():
    fleet = pd.read_csv(lt_p).merge(pd.read_csv(lr_p), on="lift", how="outer")
    fleet.to_csv(T / "lift_fleet.csv", index=False); manifest["lift_fleet.csv"] = len(fleet)

# ---------- 4. Energy + water monthly (robust join) ----------
if {"energy_monthly", "water_monthly"} <= tables:
    en = q("SELECT month, SUM(kwh) AS Energy_kWh FROM energy_monthly GROUP BY month")
    wa = q("SELECT * FROM water_monthly")
    ew = en.merge(wa, on="month", how="outer").sort_values("month")
    ew.to_csv(T / "energy_water_monthly.csv", index=False); manifest["energy_water_monthly.csv"] = len(ew)

# ---------- 5. POE by floor (cleaned sample) ----------
if "occupant_survey" in tables:
    sv = q("SELECT * FROM occupant_survey WHERE straightline_flag = 0")
    dims = ["thermal_comfort", "acoustic_privacy", "water_supply", "wifi_satisfaction",
            "lan_reliability", "safety_feeling", "overall_satisfaction"]
    poe = sv.groupby("floor")[dims].mean().round(2).reset_index()
    poe.to_csv(T / "poe_by_floor.csv", index=False); manifest["poe_by_floor.csv"] = len(poe)

# ---------- 6. Wi-Fi QoS by floor (live network) ----------
if "wifi_performance" in tables:
    w = q("SELECT * FROM wifi_performance")
    wf = w.groupby("floor").agg(Uptime_pct=("uptime_pct", "mean"), RSSI_dBm=("avg_rssi_dbm", "mean"),
                                Throughput_Mbps=("avg_throughput_mbps", "mean"),
                                Peak_clients_per_AP=("peak_clients_per_ap", "max")).round(1).reset_index()
    wf.to_csv(T / "wifi_by_floor.csv", index=False); manifest["wifi_by_floor.csv"] = len(wf)

# ---------- 7. Complaints Pareto + monthly trend ----------
if "complaints" in tables:
    c = q("SELECT * FROM complaints")
    c["month"] = pd.to_datetime(c["raised_date"]).dt.to_period("M").astype(str)
    par = c.groupby("category").agg(Tickets=("ticket_id", "count"), Total_cost_INR=("cost_inr", "sum"),
                                    Guarantee_covered_tickets=("guarantee_covered", "sum"),
                                    Avg_MTTR_days=("mttr_days", "mean")).reset_index()
    par["Avg_MTTR_days"] = par["Avg_MTTR_days"].round(1)
    par = par.sort_values("Tickets", ascending=False)
    par.to_csv(T / "complaints_pareto.csv", index=False); manifest["complaints_pareto.csv"] = len(par)
    c.groupby(["month", "category"]).size().reset_index(name="tickets") \
     .to_csv(T / "complaints_trend.csv", index=False); manifest["complaints_trend.csv"] = len(c)

# ---------- 8. Occupancy + LAN/Wi-Fi readiness by floor ----------
if "rooms" in tables:
    r = q("SELECT * FROM rooms")
    occ = r.groupby("floor").agg(Rooms=("room_id", "count"), Beds=("beds", "sum"),
                                 Occupied_beds=("occupied_beds", "sum"),
                                 LAN_points=("lan_points", "sum"),
                                 LAN_live=("lan_functional", "sum"),
                                 Avg_room_RSSI_dBm=("wifi_rssi_dbm", "mean")).reset_index()
    occ["Avg_room_RSSI_dBm"] = occ["Avg_room_RSSI_dBm"].round(1)
    occ["Occupancy_pct"] = (occ["Occupied_beds"] / occ["Beds"] * 100).round(1)
    occ.to_csv(T / "occupancy_by_floor.csv", index=False); manifest["occupancy_by_floor.csv"] = len(occ)

# ---------- 9. Direct copies of audit / plan artefacts ----------
for n in ["bhi_summary.csv", "audit_structural_floor.csv", "audit_noc_failures.csv",
          "audit_load_utilisation.csv", "audit_poe.csv", "water_roi.csv", "thermal_roi.csv",
          "energy_anomaly.csv", "pm_gaps.csv", "gantt_schedule.csv", "risk_register.csv"]:
    if (OUT / n).exists():
        shutil.copy(OUT / n, T / n); manifest[n] = len(pd.read_csv(T / n))

# ---------- 10. Asset register + purpose fulfilment (BOQ-anchored) ----------
for src, dst in [("asset_register", "asset_register.csv"), ("purpose_fulfilment", "purpose_fulfilment.csv")]:
    if src in tables:
        df = q(f"SELECT * FROM {src}")
        df.to_csv(T / dst, index=False); manifest[dst] = len(df)

conn.close()
print("=" * 70)
print("TABLEAU EXTRACTS READY ->", T)
print("=" * 70)
for k in sorted(manifest):
    print(f"  {k:<32} {manifest[k]:>5} rows")
print(f"\nTotal extracts: {len(manifest)}")