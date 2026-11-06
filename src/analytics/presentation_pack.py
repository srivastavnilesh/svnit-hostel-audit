"""Presentation Pack: one command -> timestamped run log + professor-ready report.
Runs Phase 2 (audit) + Phase 3 (optimisation), mirrors console output to
outputs/logs/presentation_run_<date>.log, then compiles outputs/audit_report.md
with the full compliance reference register."""
import subprocess, sys
from pathlib import Path
from datetime import date
import pandas as pd

ROOT   = Path(__file__).resolve().parents[2]
OUT    = ROOT / "outputs"
LOGD   = OUT / "logs"; LOGD.mkdir(parents=True, exist_ok=True)
TODAY  = date.today().isoformat()
LOGF   = LOGD / f"presentation_run_{TODAY}.log"
REPORT = OUT / "audit_report.md"
SCRIPTS = ["src/analytics/audit_engine.py", "src/analytics/predictive_optimization.py"]

buf = [f"# Presentation run log - {TODAY}",
       "Project: Building Safety & Feasibility Assessment - Atal Bihari Bajpayee Bhavan, SVNIT Surat", ""]
for s in SCRIPTS:
    buf.append(f"\n===== EXEC {s} =====\n")
    p = subprocess.run([sys.executable, str(ROOT / s)], cwd=ROOT, capture_output=True, text=True)
    buf.append(p.stdout)
    if p.stderr.strip():
        buf.append("--- stderr ---\n" + p.stderr)
    print(p.stdout)
    if p.returncode:
        print(p.stderr)
LOGF.write_text("\n".join(buf), encoding="utf-8")
print(f"\n[log saved]    {LOGF}")

def md(df):
    c = list(df.columns)
    return "\n".join(["| " + " | ".join(c) + " |", "| " + " | ".join(["---"] * len(c)) + " |"] +
                     ["| " + " | ".join(str(v) for v in r) + " |" for r in df.values])

def sec(csv, title, idx0=False):
    p = OUT / csv
    if not p.exists():
        return ""
    df = pd.read_csv(p, index_col=0) if idx0 else pd.read_csv(p)
    if idx0:
        df = df.reset_index()
    return f"\n## {title}\n\n{md(df)}\n"

rep = f"""# Building Safety & Feasibility Audit Report
**Asset:** Atal Bihari Bajpayee Bhavan - 500-seater EWS Boys Hostel, SVNIT Surat (G+6, 9,478.43 sqm)
**Statutory refs:** CPWD NIT 07/EE(C)-Surat/SE-Vadodara/ADG(RM)/2020-21 | SMC Fire NOC FireNOC/2023-2024/1108 (issued 09/08/2023, 3-yr validity)
**Codes:** IS 13311-1:1992 | IS 456:2000 | IS 875-2 | IS 1172:1993 | NBC 2016 Part 4 | CPWD Cl. 7.1 (10-yr WP guarantee), Cl. 11.6 (UPV acceptance)
**Run date:** {TODAY} | **Data basis:** seeded, reproducible digital twin anchored to BOQ quantities
{sec('bhi_summary.csv', '1. Building Health Index (governance-capped)')}
{sec('audit_structural_floor.csv', '2. Structural health by floor (IS 13311-1 / IS 456)')}
{sec('audit_noc_failures.csv', '3. SMC Fire NOC - non-compliant conditions')}
{sec('audit_lift_traffic.csv', '4. Lift traffic engineering (EN 81-20 method)')}
{sec('predictive_lift_risk.csv', '5. Lift reliability vs CPWD 8-h benchmark')}
{sec('audit_load_utilisation.csv', '6. Load utilisation & change-of-use flags (IS 875-2)')}
{sec('water_roi.csv', '7. Water leakage ROI (IS 1172)')}
{sec('thermal_roi.csv', '8. Sixth-floor thermal / cool-roof case')}
{sec('pm_gaps.csv', '9. Preventive-maintenance compliance gaps')}
{sec('audit_poe.csv', '10. Post-occupancy evaluation means (cleaned sample)', idx0=True)}
## 11. Compliance reference register
| Ref | Requirement | Audit status |
| --- | --- | --- |
| SMC NOC Cond. 30 | Quarterly fire drill with maintained log | 4 drills/yr - OK |
| SMC NOC Cond. 18 / 20 | Staircases & corridors free of encroachment | FAIL - shoe racks, cycles |
| SMC NOC Cond. 23 | Emergency lighting operational | FAIL - 2 dead units, 3rd fl |
| SMC NOC Cond. 34 | Trained fire manpower round-the-clock | PARTIAL - single shift |
| SMC NOC Cond. 41 | Balcony grills openable for rescue | FAIL - padlocked fl 4 & 6 |
| CPWD Cl. 7.1.3 | WP annual inspection by guarantee firm; 7-day rectification | Bond active to 2033 - seepage tickets at zero cost |
| CPWD Cl. 11.6 | UPV routine test; accept Good/Excellent only | Terrace 83.3% Good+Exc; 2 elements flagged for re-test |
| CPWD lift eligibility | Avg downtime <= 8 h minor / <= 7 d major | All 4 lifts PASS on cleaned stats |
| IS 1172:1993 | 135 LPCD domestic norm | Measured ~201 LPCD - leakage ROI opened |
"""
REPORT.write_text(rep, encoding="utf-8")
print(f"[report saved] {REPORT}")