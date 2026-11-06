"""Phase 1 v3: Robust Digital Twin - Atal Bihari Bajpayee Bhavan (SVNIT Surat).
Anchors: CPWD NIT 07/2020-21 BOQ, SMC Fire NOC 2023-24/1108, IMD Surat normals.
Robustness: seeded RNG, clipped distributions, flagged (not deleted) outliers,
data_quality_log for full lineage. Handover 15-Jul-2023 -> age 3.3 yrs at audit."""
import numpy as np, pandas as pd, sqlite3
from pathlib import Path
from datetime import date, timedelta

rng = np.random.default_rng(42)
DB = Path("data/hostel_digital_twin.db"); DB.parent.mkdir(parents=True, exist_ok=True)
TODAY, HANDOVER = date(2026, 11, 6), date(2023, 7, 15)
FLOORS = ["Ground","First","Second","Third","Fourth","Fifth","Sixth"]
CLIM = {1:(29,2),2:(32,1),3:(36,0),4:(39,1),5:(41,10),6:(37,120),
        7:(32,275),8:(31,250),9:(32,160),10:(35,25),11:(33,5),12:(30,1)}
def cn(mu, sd, lo, hi):   # clipped normal = outlier-controlled by construction
    return float(np.clip(rng.normal(mu, sd), lo, hi))
def occ_factor(d):
    if (d.month==5 and d.day>=20) or (d.month==6 and d.day<=20): return 0.30
    if (d.month==12 and d.day>=20) or (d.month==1 and d.day<=5): return 0.30
    return 1.0
def warranty(years): return (HANDOVER.replace(year=HANDOVER.year+years)).isoformat()
dq = []  # data quality lineage

# ---------- 1. ASSET REGISTER (BOQ-anchored, warranty clocks) ----------
A = [
 ("LIFT-01","Lift","16-pax gearless 1088 kg, 1.5 m/s, 7 stops","Lobby A",warranty(0),"AMC active","Operational"),
 ("LIFT-02","Lift","16-pax gearless 1088 kg, 1.5 m/s, 7 stops","Lobby B",warranty(0),"AMC active","Operational"),
 ("LIFT-03","Lift","20-pax hospital/auto 1360 kg, 1.0 m/s","Lobby A",warranty(0),"AMC active","Operational"),
 ("LIFT-04","Lift","20-pax hospital/auto 1360 kg, 1.0 m/s","Lobby B",warranty(0),"AMC active","Operational"),
 ("PUMP-DOM-01","Pump","Submersible 1040 LPM @30 m","UG sump",warranty(2),"Expired 2025","Operational"),
 ("PUMP-DOM-02","Pump","Submersible 1040 LPM @30 m","UG sump",warranty(2),"Expired 2025","Standby"),
 ("PUMP-FL-01","Pump","Flushing submersible 7.5 HP","UG sump",warranty(2),"Expired 2025","Operational"),
 ("PUMP-FL-02","Pump","Flushing submersible 7.5 HP","UG sump",warranty(2),"Expired 2025","Standby"),
 ("PUMP-FIRE-01","Fire pump","900 LPM @35 m multistage","Terrace",warranty(0),"NOC-linked","Operational"),
 ("PUMP-FIRE-02","Fire pump","900 LPM @35 m multistage","Terrace",warranty(0),"NOC-linked","Operational"),
 ("LT-MAIN","Panel","630A FP MCCB incomer, 800A busbar","GF elec rm",warranty(0),"-","Operational"),
 ("LT-BWING","Panel","200A incomer, B-wing","GF elec rm",warranty(0),"-","Operational"),
 ("FIRE-PANEL","Fire alarm","2-loop addressable, 240-device","GF lobby",warranty(0),"NOC-linked","Operational"),
 ("DET-ARRAY","Fire alarm","161 photo-thermal addressable","All floors",warranty(0),"NOC-linked","154/161 pass"),
 ("HYD-ARRAY","Fire","32 SS hydrant valves + 16 hose reels","Stairs/floors",warranty(0),"NOC-linked","Operational"),
 ("EXT-ARRAY","Fire","25x4kg ABC + 25x4.5kg CO2","All floors",warranty(0),"Refill due 12/2026","Serviceable"),
 ("TANK-TR","Tank","50 kL polyethylene terrace","Terrace",warranty(0),"-","Operational"),
 ("TANK-UG","Tank","150 kL RCC sump (assumed)","UG",warranty(0),"-","Operational"),
 ("WIFI-APS","ICT","56 APs (51 in + 5 out) Wi-Fi6 + NMS","All floors",warranty(5),"Warranty to 2028","Operational"),
 ("LAN-PTS","ICT","524 CAT-6 points (2/room + common)","All rooms",warranty(0),"-","509/524 live"),
 ("FAN-BLDC","Electrical","307 BLDC fans BEE 5-star","Rooms",warranty(5),"Warranty to 2028","Operational"),
 ("EXH-FAN","Electrical","181 heavy-duty exhaust 300 mm","Toilets/lift rm",warranty(0),"-","171/181 live"),
 ("LED-ARRAY","Electrical","~2,050 LED luminaires","Building",warranty(5),"Warranty to 2028","Operational"),
 ("STREET-LT","Electrical","20 octagonal poles, 35-40W LED","Periphery",warranty(5),"Warranty to 2028","Operational"),
 ("WP-TERRACE","Civil","Brick-bat coba + china mosaic, 1920 sqm","Terrace",warranty(10),"Bond to 2033","Guarantee-active"),
 ("STAIR-01","Egress","1.5 m ventilated staircase","Wing A",warranty(0),"NOC-linked","Encroached"),
 ("STAIR-02","Egress","1.5 m ventilated staircase","Wing B",warranty(0),"NOC-linked","Encroached"),
 ("RWH-BORE","Civil","120 m borewell + recharge pit","Site",warranty(0),"-","Operational"),
]
df_assets = pd.DataFrame(A, columns=["asset_id","category","spec","location","warranty_expiry","warranty_status","current_status"])

# ---------- 2. ROOMS + LAN + per-room Wi-Fi RSSI ----------
rooms, rid = [], 0
for floor, typ, n in [("Ground","Student",10),("Ground","Guest",4),("Ground","Differently-abled",4),
                      ("First","Student",32)] + [(f,"Student",40) for f in FLOORS[2:]]:
    for i in range(1, n+1):
        rid += 1
        p = 0.955 if typ == "Student" else 0.75
        occ = 2 if rng.random() < p else int(rng.integers(0, 2))
        lan_ok = 2 if rng.random() < 0.94 else (1 if rng.random() < 0.7 else 0)
        rssi = cn(-52 if i % 4 else -58, 4, -71, -45)   # corridor-end rooms weaker
        rooms.append((f"{floor[0]}-{i:02d}", floor, typ, 2, occ, 2, lan_ok, round(rssi,1)))
df_rooms = pd.DataFrame(rooms, columns=["room_id","floor","room_type","beds","occupied_beds","lan_points","lan_functional","wifi_rssi_dbm"])
OCC = int(df_rooms.occupied_beds.sum())

# ---------- 3. STRUCTURAL NDT (IS 13311-1) + controlled re-test flags ----------
ndt = []
for fl in FLOORS:
    for el in ["Column","Beam","Slab","Wall"]:
        for k in range(1, 9):
            damp = 1 if (fl=="Sixth" and rng.random()<0.28) or (fl=="Fifth" and rng.random()<0.08) else 0
            ndt.append((fl, el, f"{el[:2]}-{fl[:2]}-{k:02d}",
                        round(cn(4.35 - (0.30 if (fl=="Sixth" and el=="Slab") else 0) - 0.12*damp, 0.22, 3.1, 4.8), 2),
                        round(cn(29.5, 3.0, 21, 38), 1), round(cn(4.0, 2.2, 0.5, 11.0), 1),
                        round(cn(0.08, 0.06, 0.0, 0.35), 2), damp, 0, "Sound" if not damp else "Damp patch near khurra"))
for k in range(1, 13):
    ndt.append(("Terrace","Slab",f"TF-SL-{k:02d}", round(cn(3.9,0.3,3.0,4.5),2), round(cn(27,2.5,20,34),1),
                round(cn(5.0,2.5,1,12),1), round(cn(0.28,0.12,0.10,0.55),2), 1, 0, "Crack+seepage: guarantee claim"))
ndt[17] = (*ndt[17][:3], 2.88, 23.5, 6.2, 0.10, 0, 1, "Doubtful UPV - re-test scheduled")   # flagged outlier
ndt[96] = (*ndt[96][:3], 2.94, 24.1, 5.8, 0.05, 0, 1, "Doubtful UPV - re-test scheduled")
df_ndt = pd.DataFrame(ndt, columns=["floor","element","tag","upv_km_s","rebound_mpa","carbonation_mm","crack_width_mm","damp_patch","retest_flag","remark"])
dq.append(("structural_ndt","2 doubtful UPV readings retained with retest_flag=1",2,"Excluded from floor means; re-test Dec-2026"))

# ---------- 4. MEP DAILY (4 lifts, 6 pumps, main panel) + injected outliers ----------
mep, d0 = [], TODAY - timedelta(days=365)
LIFTS = {"LIFT-01":330,"LIFT-02":320,"LIFT-03":250,"LIFT-04":235}
FR = {"LIFT-01":0.012,"LIFT-02":0.010,"LIFT-03":0.016,"LIFT-04":0.014}
for i in range(365):
    d = d0 + timedelta(days=i); tmax, rain = CLIM[d.month]; of = occ_factor(d)
    wf = 1.0 if d.weekday() < 5 else 0.86
    for L, base in LIFTS.items():
        trips = int(cn(base*of*wf, base*0.06, 0, base*1.35))
        fault = rng.random() < FR[L]*(1.25 if d.month in (5,6,7) else 1.0)
        dt = round(cn(3.2, 2.5, 0.5, 48), 1) if fault else 0.0
        mep.append((d.isoformat(), L, "daily_trips", trips, dt, 0, "Door sensor/ARD fault" if fault else ""))
    for P, base in {"PUMP-DOM-01":4.3,"PUMP-DOM-02":4.0,"PUMP-FL-01":2.0,"PUMP-FL-02":1.9}.items():
        rh = cn(base*of*(1.15 if d.month in (4,5,6) else 1.0), 0.35, 0, base*2)
        dry = rng.random() < (0.015 if d.month in (4,5) else 0.002)
        mep.append((d.isoformat(), P, "run_hours", round(rh,2), 2.0 if dry else 0.0, 0, "Dry-run trip (low sump)" if dry else ""))
    load = cn(58 + 13*max(0,tmax-32)/9*of + 8*of, 3.5, 40, 88)
    mep.append((d.isoformat(),"LT-MAIN","load_pct", round(load,1), 0.0, 0, ""))
    mep.append((d.isoformat(),"LT-MAIN","max_temp_c", round(cn(34+(tmax-29)*0.6+load*0.09, 1.2, 36, 56),1), 0.0, 0, ""))
mep.append(("2026-03-14","LIFT-03","downtime_hours_override",0,720.0,1,"Decimal-entry error: 72.0h logged as 720h"))
mep.append(("2026-07-02","LT-MAIN","max_temp_c",95.4,0.0,1,"Sensor fault spike; IR scan confirmed 49C"))
mep.append(("2026-01-19","LIFT-01","daily_trips",12041,0.0,1,"Controller counter reset artefact"))
df_mep = pd.DataFrame(mep, columns=["date","asset_id","metric","value","downtime_hours","is_outlier","fault_note"])
dq.append(("mep_daily","3 injected anomalies flagged is_outlier=1",3,"Winsorised/excluded in Phase 3 reliability stats"))

# ---------- 5. ENERGY (floor sub-meters) + WATER ----------
ew, y, m = [], 2024, 10
SHARE = {"Ground":0.18,"First":0.12,"Second":0.14,"Third":0.14,"Fourth":0.14,"Fifth":0.14,"Sixth":0.14}
for _ in range(24):
    tmax, rain = CLIM[m]; of = 0.45 if m in (5,6,12,1) else 1.0
    occ_m = int(OCC*of)
    day = (occ_m*2.4 + 1850 + occ_m*0.35*max(0, tmax-33))*30.4
    for f, s in SHARE.items():
        ew.append((f"{y}-{m:02d}", f, int(day*s*cn(1,0.03,0.9,1.1))))
    m += 1
    if m == 13: m, y = 1, 2025
df_ew = pd.DataFrame(ew, columns=["month","floor_db","kwh"])
wat = []
y, m = 2024, 10
for _ in range(24):
    tmax, _ = CLIM[m]; of = 0.45 if m in (5,6,12,1) else 1.0
    occ_m = int(OCC*of)
    kld = round(occ_m*0.135*1.42*(1.12 if m in (4,5,6) else 1.0) + cn(0,2.5,-6,6), 1)
    leaks = int(rng.poisson(1.2 if m in (6,7,8,9) else 0.7))
    wat.append((f"{y}-{m:02d}", occ_m, kld, round(kld*1000/max(1,occ_m),0), leaks))
    m += 1
    if m == 13: m, y = 1, 2025
wat[14] = (wat[14][0], wat[14][1], round(wat[14][2]*1.35,1), 273, 4)  # night-flow leak event
dq.append(("water_monthly","1 night-flow anomaly (Mar-26) retained as leak event",1,"Root cause: flushing line joint; repaired in 6 days"))
df_wat = pd.DataFrame(wat, columns=["month","avg_occupancy","water_kld","water_lpcd","leak_events"])

# ---------- 6. WI-FI PERFORMANCE (live network QoS) ----------
wifi = []
y, m = 2024, 10
for _ in range(24):
    exam = m in (4,11)
    for f in FLOORS:
        wifi.append((f"{y}-{m:02d}", f, 8,
                     round(cn(99.1 if f!="Sixth" else 98.4, 0.7, 95.5, 99.9),2),
                     round(cn(-51 if f in ("Ground","First") else -56, 3, -68, -45),1),
                     round(cn(58 if not exam else 44, 8, 25, 85),1),
                     int(cn(74 if not exam else 92, 9, 40, 110))))
    m += 1
    if m == 13: m, y = 1, 2025
df_wifi = pd.DataFrame(wifi, columns=["month","floor","ap_count","uptime_pct","avg_rssi_dbm","avg_throughput_mbps","peak_clients_per_ap"])
dq.append(("wifi_performance","Exam-month throughput dips retained (real congestion)",24,"Modelled, not errors"))

# ---------- 7. FIRE: 42-condition audit, detectors, drills, false alarms ----------
fails = {18:(40,"Shoe racks/cycles encroaching staircase B, fl 2-4"),
         20:(60,"Study tables/cycles obstructing corridor, fl 3 & 5"),
         23:(70,"2 emergency luminaires dead-battery, 3rd fl stair"),
         34:(85,"Trained fire operator single-shift only"),
         41:(50,"Balcony grills padlocked, fl 4 & 6 (not openable)")}
df_cond = pd.DataFrame([(n, *fails.get(n, (100, "Compliant"))) for n in range(1,43)],
                       columns=["noc_condition_no","compliance_score","remark"])
det = []
for i in range(1, 162):
    r = rng.random()
    res = "Fail" if r < 0.031 else ("Overdue" if r < 0.043 else "Pass")
    det.append((f"DET-{i:03d}", 1 if i <= 80 else 2, FLOORS[min(6,(i-1)//23)], "Photo-thermal", "2026-07-14", res))
df_det = pd.DataFrame(det, columns=["detector_id","loop","floor","type","test_date","result"])
df_drills = pd.DataFrame([
 ("2025-09-18",452,8.2,"Staircase B bottleneck observed"),
 ("2025-12-15",466,7.4,"Wardens retrained post-drill"),
 ("2026-03-10",471,6.8,"Mock smoke at 2nd-fl pantry"),
 ("2026-08-12",483,6.1,"Joint drill with SMC Fire Brigade (NOC renewal)")],
 columns=["drill_date","participants","evacuation_minutes","remarks"])
df_false = pd.DataFrame([
 ("2025-11-04","GF pantry","Steam ingress",6),("2026-01-22","3rd fl corridor","Dust during deep-clean",4),
 ("2026-06-19","6th fl lobby","Monsoon humidity",7),("2026-07-08","5th fl lobby","Monsoon humidity",5),
 ("2026-07-27","6th fl passage","Humidity + detector ageing",9),("2026-08-15","2nd fl lobby","MCP malicious activation",3),
 ("2026-09-03","4th fl corridor","Dust",4),("2026-09-21","GF kitchen","Steam",6),("2026-10-11","6th fl lobby","Humidity",5)],
 columns=["date","zone","cause","duration_min"])

# ---------- 8. COMPLAINTS (seasonal, warranty-aware costing) ----------
cats = ["Seepage/Damp","Lift fault","Exhaust fan","LAN/Wi-Fi","Plumbing leak","Electrical trip","Water pressure","Civil/misc"]
comp, tid = [], 1000
for _ in range(170):
    d = TODAY - timedelta(days=int(rng.integers(0,365))); tmax, rain = CLIM[d.month]
    w = np.array([0.6+2.6*rain/275, 1.5, 1.2, 1.3, 1.5, 1.0, 0.9+0.8*max(0,tmax-35)/8, 1.1]); w /= w.sum()
    c = rng.choice(cats, p=w)
    mttr = int(np.clip(rng.lognormal(1.1,0.7), 1, 21 if c=="Seepage/Damp" else 8))
    guar = 1 if (c=="Seepage/Damp" or c=="Electrical trip") else 0   # WP bond to 2033 / LED warranty to 2028
    cost = 0 if guar else int(np.clip(rng.lognormal(7.5,0.8), 300, 25000))
    comp.append((f"CM-{tid}", d.isoformat(), c, rng.choice(FLOORS), mttr,
                 "Closed" if rng.random()<0.88 else "Open", cost, guar)); tid += 1
comp.append(("CM-1201","2026-06-30","Seepage/Damp","Sixth",14,"Closed",0,1))  # duplicate of CM-1188
dq.append(("complaints","1 duplicate ticket retained for audit trail",1,"Deduplicated in Phase 3 MTTR stats"))
df_comp = pd.DataFrame(comp, columns=["ticket_id","raised_date","category","floor","mttr_days","status","cost_inr","guarantee_covered"])

# ---------- 9. PM SCHEDULE COMPLIANCE ----------
df_pm = pd.DataFrame([
 ("Lifts (4)","Quarterly AMC","2026-10-05","2027-01-05",100),
 ("Fire pumps churn","Monthly","2026-11-01","2026-12-01",92),
 ("Detector test","Annual","2026-07-14","2027-07-14",100),
 ("Extinguisher refill","Half-yearly","2026-06-20","2026-12-20",100),
 ("Tank cleaning","Half-yearly","2026-09-12","2027-03-12",100),
 ("DG changeover test","Monthly","2026-10-28","2026-11-28",88),
 ("Wi-Fi NMS health","Weekly","2026-11-02","2026-11-09",95),
 ("Exhaust fans","Quarterly","2026-09-25","2026-12-25",84)],
 columns=["asset","frequency","last_done","next_due","compliance_pct"])

# ---------- 10. OCCUPANT SURVEY (500, Wi-Fi live) ----------
sv = []
for sid in range(1, 501):
    fl = rng.choice(FLOORS[1:], p=[0.13,0.2,0.2,0.2,0.2,0.07])
    therm = cn(3.5 - (0.95 if fl=="Sixth" else 0.35 if fl=="Fifth" else 0), 0.8, 1, 5)
    row = (sid, fl, int(round(therm)), int(round(cn(3.4,0.9,1,5))), int(round(cn(3.2,0.9,1,5))),
           int(round(cn(3.4,0.9,1,5))), int(round(cn(4.0,0.7,1,5))), int(round(cn(4.0,0.7,1,5))))
    flag = 1 if sid in (77,143,268,311,402,455) else 0     # straight-liners
    if flag: row = (sid, fl, 5,5,5,5,5,5)
    sv.append(row + (int(round(np.clip(np.mean(row[2:])+cn(0,0.3,-1,1),1,5))), flag))
df_sv = pd.DataFrame(sv, columns=["student_id","floor","thermal_comfort","acoustic_privacy","water_supply","wifi_satisfaction","lan_reliability","safety_feeling","overall_satisfaction","straightline_flag"])
dq.append(("occupant_survey","6 straight-line respondents flagged",6,"Excluded from POE means"))

# ---------- 11. PURPOSE FULFILMENT ----------
df_pf = pd.DataFrame([
 ("Bed occupancy",478,500,"beds",">=90%","OK"),
 ("Dining seats/sitting",156,478,"seats","3 sittings","OK"),
 ("Guest room utilisation",34,60,"%",">=50%","UNDER"),
 ("DA rooms occupied",2,4,"rooms","4","UNDER"),
 ("Sports rm peak users",92,60,"persons","<=60","OVERCROWDED"),
 ("LAN points live",509,524,"points",">=98%","MARGINAL"),
 ("Wi-Fi APs operational",56,56,"APs","56","OK"),
 ("Wi-Fi peak clients/AP",92,100,"clients","<=100 (exam wk)","MARGINAL"),
 ("Lift peak wait",75,60,"sec","<=60 (dormitory)","UNDER"),
 ("Per-capita water",196,135,"LPCD","<=135 IS 1172","OVER-leakage"),
 ("Evacuation time",6.1,5.0,"min","<=5","UNDER")],
 columns=["metric","actual","target","unit","norm","status"])

# ---------- WRITE ----------
conn = sqlite3.connect(DB)
for name, df in [("asset_register",df_assets),("rooms",df_rooms),("structural_ndt",df_ndt),
                 ("mep_daily",df_mep),("energy_monthly",df_ew),("water_monthly",df_wat),
                 ("wifi_performance",df_wifi),("fire_noc_conditions",df_cond),("detector_tests",df_det),
                 ("fire_drills",df_drills),("false_alarms",df_false),("complaints",df_comp),
                 ("pm_schedule",df_pm),("occupant_survey",df_sv),("purpose_fulfilment",df_pf),
                 ("data_quality_log",pd.DataFrame(dq, columns=["table","issue","rows_affected","handling"]))]:
    df.to_sql(name, conn, if_exists="replace", index=False)
conn.commit(); conn.close()
print(f"✅ Digital Twin v3 | Beds {OCC}/500 | Rooms {len(df_rooms)} | MEP rows {len(df_mep):,}")
print(f"   Flagged outliers: mep={int(df_mep.is_outlier.sum())}, ndt retest={int(df_ndt.retest_flag.sum())}, survey={int(df_sv.straightline_flag.sum())}")
print(f"   Tables: 16 | Warranty clocks: WP->2033, LED->2028, Alu/Sanitary->expired 2025")