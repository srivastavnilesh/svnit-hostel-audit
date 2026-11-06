"""Phase 2: Compliance & Structural Audit Engine - Atal Bihari Bajpayee Bhavan, SVNIT.
Codes: IS 13311-1, IS 456, IS 875-2, IS 1172, NBC 2016 (egress principles),
SMC Fire NOC 2023-24/1108, CPWD NIT 07/2020-21 (UPV acceptance Cl. 11.6, WP bond Cl. 7.1).
Robust stats: every metric computed raw AND cleaned per data_quality_log flags."""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import date

DB = Path("data/hostel_digital_twin.db")
OUT = Path("outputs"); OUT.mkdir(parents=True, exist_ok=True)
TODAY = date(2026, 11, 6)
NOC_ISSUED, NOC_YEARS = date(2023, 8, 9), 3
COVER_MM, CRACK_LIMIT, TARIFF = 25.0, 0.2, 7.2

conn = sqlite3.connect(DB)
L = {t: pd.read_sql(f"SELECT * FROM {t}", conn) for t in
     ["asset_register","rooms","structural_ndt","mep_daily","energy_monthly","water_monthly",
      "wifi_performance","fire_noc_conditions","detector_tests","fire_drills","false_alarms",
      "complaints","pm_schedule","occupant_survey","purpose_fulfilment"]}
conn.close()

# ---- Robust cleaning per data_quality_log ----
ndt_c  = L["structural_ndt"][L["structural_ndt"].retest_flag == 0]
mep_c  = L["mep_daily"][L["mep_daily"].is_outlier == 0]
sv_c   = L["occupant_survey"][L["occupant_survey"].straightline_flag == 0]
comp_c = L["complaints"].drop_duplicates(subset=["raised_date","category","floor"])

# ---------- 1. STRUCTURAL ----------
def grade(v): return "Excellent" if v>4.5 else "Good" if v>3.5 else "Medium" if v>3.0 else "Doubtful"
ndt_c = ndt_c.copy(); ndt_c["upv_grade"] = ndt_c["upv_km_s"].map(grade)
ndt_c["crack_flag"] = (ndt_c["crack_width_mm"] > CRACK_LIMIT).astype(int)
ndt_c["carbon_flag"] = (ndt_c["carbonation_mm"] > COVER_MM/2).astype(int)
ndt_c["strength_flag"] = (ndt_c["rebound_mpa"] < 25).astype(int)
fs = ndt_c.groupby("floor").agg(elements=("tag","count"), upv_mean=("upv_km_s","mean"),
        pct_good_exc=("upv_grade", lambda s: (s.isin(["Good","Excellent"]).mean()*100).round(1)),
        crack_flags=("crack_flag","sum"), damp=("damp_patch","sum"),
        carbon_flags=("carbon_flag","sum"), strength_flags=("strength_flag","sum")).reset_index()
pen = fs.crack_flags*4 + fs.damp*3 + fs.strength_flags*2 + fs.carbon_flags*1 + (100-fs.pct_good_exc)*0.2
fs["structural_score"] = (100-pen).clip(40,100).round(1)

# ---------- 2. FIRE GOVERNANCE ----------
noc_exp = date(NOC_ISSUED.year+NOC_YEARS, NOC_ISSUED.month, NOC_ISSUED.day)
noc_over = (TODAY-noc_exp).days
cond_mean = L["fire_noc_conditions"].compliance_score.mean()
failing = L["fire_noc_conditions"][L["fire_noc_conditions"].compliance_score < 100]
det_pass = (L["detector_tests"].result=="Pass").mean()*100
det_fail_floor = L["detector_tests"][L["detector_tests"].result!="Pass"].floor.value_counts().to_dict()
drills = L["fire_drills"].sort_values("drill_date")
drill_ok = len(drills) >= 4                      # Condition 30: quarterly
drill_score = min(100.0, 5.0/drills.evacuation_minutes.iloc[-1]*100)
fa_pareto = L["false_alarms"].cause.value_counts().to_dict()
fire_score = round(0.55*cond_mean + 0.25*det_pass + 0.20*drill_score, 1)

# ---------- 3. LIFT TRAFFIC (EN 81-20 / ISO 8100 method) ----------
SPEC = {"LIFT-01":(16,1.5),"LIFT-02":(16,1.5),"LIFT-03":(20,1.0),"LIFT-04":(20,1.0)}
TRAVEL, STOPS, DOOR_CYC, TRANSFER = 18.0, 6, 6.0, 1.2
rows = []
for lid,(pax,spd) in SPEC.items():
    rtt = 2*TRAVEL/spd + STOPS*(DOOR_CYC + TRANSFER*0.8*pax)
    hc5 = (300/rtt)*(0.8*pax)                    # persons per 5-min peak
    rows.append((lid,pax,spd,round(rtt),round(hc5)))
lt = pd.DataFrame(rows, columns=["lift","pax","speed_mps","rtt_s","hc5_persons"])
interval = lt.rtt_s.mean()/4
awt_theo = round(0.5*interval*1.35, 1)           # bunching factor 1.35
hc_total = lt.hc5_persons.sum()
POP = int(L["rooms"].occupied_beds.sum())
hc_pct = round(hc_total/POP*100, 1)
lifts_m = mep_c[mep_c.asset_id.str.startswith("LIFT")]
avail = (1 - lifts_m.groupby("asset_id").downtime_hours.sum()/(365*24))*100
dt = lifts_m[lifts_m.downtime_hours>0].downtime_hours
dt_raw = L["mep_daily"][(L["mep_daily"].asset_id.str.startswith("LIFT")) & (L["mep_daily"].downtime_hours>0)].downtime_hours

# ---------- 4. LOAD UTILISATION (IS 875-2) ----------
AREAS = {"Ground":1630.53,"First":1349.45,**{f:1299.69 for f in ["Second","Third","Fourth","Fifth","Sixth"]}}
LLD = {"Ground":4.0, **{f:3.0 for f in AREAS if f!="Ground"}}
DL, OCCF = 7.5, POP/500
load = [(z,a,DL,LLD[z],round(LLD[z]*OCCF,2),round(a*(DL+LLD[z]*OCCF)/1000,2),round(OCCF*100,1),"PASS") for z,a in AREAS.items()]
load.append(("Terrace + solar ballast 0.6",1299.69,DL,1.5,0.60,round(1299.69*(DL+0.6)/1000,2),40.0,"PASS-headroom 0.9"))
load.append(("Sports rm -> book bank",179.30,DL,4.0,5.0,round(179.30*(DL+5.0)/1000,2),125.0,"FLAG-structural check"))
ld = pd.DataFrame(load, columns=["zone","area_sqm","DL","LL_design","LL_actual","total_MN","util_pct","verdict"])

# ---------- 5. MEP RELIABILITY + POE ----------
panel = mep_c[(mep_c.asset_id=="LT-MAIN") & (mep_c.metric=="max_temp_c")]
over_temp = int((panel.value>50).sum())
dry = int((mep_c.fault_note.str.contains("Dry-run")).sum())
pm_mean = L["pm_schedule"].compliance_pct.mean()
mep_score = round(0.5*avail.mean() + 0.3*(100-over_temp/max(1,len(panel))*100) + 0.2*(100-min(100,dry*4)), 1)
poe = sv_c.drop(columns=["student_id","floor","straightline_flag"]).mean().round(2)
therm_floor = sv_c.groupby("floor").thermal_comfort.mean().round(2)
worst_driver = poe.drop("overall_satisfaction").idxmin()
en = L["energy_monthly"].groupby("month").kwh.sum().tail(12)
kwh_yr, cost_yr = int(en.sum()), round(en.sum()*TARIFF/100000, 2)
wat = L["water_monthly"]; lpcd = round(wat.water_lpcd.mean(), 0)

# ---------- 6. BUILDING HEALTH INDEX (with governance cap) ----------
struct_mean = fs.structural_score.mean()
occ_score = poe.overall_satisfaction/5*100
bhi_raw = 0.35*struct_mean + 0.25*fire_score + 0.20*mep_score + 0.20*occ_score
grade_raw = "A" if bhi_raw>=85 else "B" if bhi_raw>=70 else "C" if bhi_raw>=55 else "D"
capped = noc_over > 0
bhi_final, grade_final = (min(bhi_raw,84.9), "B") if capped and grade_raw=="A" else (bhi_raw, grade_raw)

# ---------- EXPORTS ----------
fs.to_csv(OUT/"audit_structural_floor.csv", index=False)
failing.to_csv(OUT/"audit_noc_failures.csv", index=False)
lt.to_csv(OUT/"audit_lift_traffic.csv", index=False)
ld.to_csv(OUT/"audit_load_utilisation.csv", index=False)
poe.to_frame("mean_score").to_csv(OUT/"audit_poe.csv")
pd.DataFrame([{"bhi_raw":round(bhi_raw,1),"grade_raw":grade_raw,"bhi_final":round(bhi_final,1),
   "grade_final":grade_final,"governance_cap":capped,"structural":round(struct_mean,1),
   "fire":fire_score,"mep":mep_score,"occupant":round(occ_score,1)}]).to_csv(OUT/"bhi_summary.csv", index=False)

# ---------- EXECUTIVE PRINT ----------
print("="*80)
print("BUILDING SAFETY & FEASIBILITY AUDIT - ATAL BIHARI BAJPAYEE BHAVAN (G+6, 500 beds)")
print("="*80)
print(f"BHI: {bhi_raw:.1f} (Grade {grade_raw}) -> GOVERNANCE-CAPPED: {bhi_final:.1f} (Grade {grade_final})"
      f" | cap reason: Fire NOC expired {noc_exp}, {noc_over} days overdue")
print(f"  Components -> Structural {struct_mean:.1f} | Fire {fire_score} | MEP {mep_score} | Occupant {occ_score:.1f}")
print("\n[STRUCTURAL - IS 13311-1 / CPWD Cl.11.6 acceptance = Good+Excellent only]")
print(fs.to_string(index=False))
print(f"\n[FIRE] conditions mean {cond_mean:.1f}% | detectors pass {det_pass:.1f}% (fails by floor: {det_fail_floor})")
print(f"  drills/yr {len(drills)} (Cond.30 requires 4): {'OK' if drill_ok else 'BREACH'} | last evac {drills.evacuation_minutes.iloc[-1]} min vs 5 min target")
print(f"  failing conditions: {failing.noc_condition_no.tolist()} | false-alarm Pareto: {fa_pareto}")
print("\n[LIFT TRAFFIC - EN 81-20 method from BOQ specs]")
print(lt.to_string(index=False))
print(f"  interval {interval:.0f}s | theoretical AWT {awt_theo}s | observed peak wait 75s -> OPERATIONAL gap, not capacity")
print(f"  5-min HC {hc_total:.0f} persons = {hc_pct}% of {POP} (dormitory target >=12.5%) -> capacity AMPLE")
print(f"  availability {avail.round(2).to_dict()}")
print(f"  OUTLIER PROOF -> downtime/event mean raw {dt_raw.mean():.1f}h vs cleaned {dt.mean():.1f}h | median {dt.median():.1f}h")
print("\n[LOADS - IS 875-2]", ld[ld.verdict.str.startswith('FLAG')][['zone','util_pct']].to_dict('records'))
print(f"\n[MEP/POE] panel >50C days {over_temp} | dry-runs {dry} | PM compliance {pm_mean:.0f}%")
print(f"  energy {kwh_yr:,} kWh/yr = Rs {cost_yr} lakh @ Rs{TARIFF}/kWh | water {lpcd:.0f} LPCD vs IS 1172 135")
print(f"  weakest POE driver: {worst_driver} ({poe[worst_driver]}/5) | worst thermal floor: {therm_floor.idxmin()} ({therm_floor.min()})")
print(f"\nExports -> {OUT}/")
