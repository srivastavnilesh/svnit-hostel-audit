# Building Safety & Feasibility Audit Report
**Asset:** Atal Bihari Bajpayee Bhavan - 500-seater EWS Boys Hostel, SVNIT Surat (G+6, 9,478.43 sqm)
**Statutory refs:** CPWD NIT 07/EE(C)-Surat/SE-Vadodara/ADG(RM)/2020-21 | SMC Fire NOC FireNOC/2023-2024/1108 (issued 09/08/2023, 3-yr validity)
**Codes:** IS 13311-1:1992 | IS 456:2000 | IS 875-2 | IS 1172:1993 | NBC 2016 Part 4 | CPWD Cl. 7.1 (10-yr WP guarantee), Cl. 11.6 (UPV acceptance)
**Run date:** 2026-11-06 | **Data basis:** seeded, reproducible digital twin anchored to BOQ quantities

## 1. Building Health Index (governance-capped)

| bhi_raw | grade_raw | bhi_final | grade_final | governance_cap | structural | fire | mep | occupant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 83.9 | B | 83.9 | B | True | 81.1 | 93.1 | 91.0 | 70.2 |


## 2. Structural health by floor (IS 13311-1 / IS 456)

| floor | elements | upv_mean | pct_good_exc | crack_flags | damp | carbon_flags | strength_flags | structural_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fifth | 32 | 4.3175 | 100.0 | 5 | 3 | 0 | 4 | 63.0 |
| First | 32 | 4.34875 | 100.0 | 0 | 0 | 0 | 1 | 98.0 |
| Fourth | 32 | 4.40875 | 100.0 | 1 | 0 | 0 | 3 | 90.0 |
| Ground | 31 | 4.325483870967742 | 100.0 | 1 | 0 | 0 | 1 | 94.0 |
| Second | 32 | 4.3953125 | 100.0 | 0 | 0 | 0 | 1 | 98.0 |
| Sixth | 32 | 4.2275 | 100.0 | 2 | 6 | 0 | 1 | 72.0 |
| Terrace | 12 | 3.895 | 83.3 | 10 | 12 | 0 | 2 | 40.0 |
| Third | 31 | 4.328387096774194 | 100.0 | 1 | 0 | 0 | 1 | 94.0 |


## 3. SMC Fire NOC - non-compliant conditions

| noc_condition_no | compliance_score | remark |
| --- | --- | --- |
| 18 | 40 | Shoe racks/cycles encroaching staircase B, fl 2-4 |
| 20 | 60 | Study tables/cycles obstructing corridor, fl 3 & 5 |
| 23 | 70 | 2 emergency luminaires dead-battery, 3rd fl stair |
| 34 | 85 | Trained fire operator single-shift only |
| 41 | 50 | Balcony grills padlocked, fl 4 & 6 (not openable) |


## 4. Lift traffic engineering (EN 81-20 method)

| lift | pax | speed_mps | rtt_s | hc5_persons |
| --- | --- | --- | --- | --- |
| LIFT-01 | 16 | 1.5 | 152 | 25 |
| LIFT-02 | 16 | 1.5 | 152 | 25 |
| LIFT-03 | 20 | 1.0 | 187 | 26 |
| LIFT-04 | 20 | 1.0 | 187 | 26 |


## 5. Lift reliability vs CPWD 8-h benchmark

| lift | faults_365d | mtbf_days | mean_dt_h | median_dt_h | cpwd_check | risk_score | recommended_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIFT-01 | 3 | 121.7 | 3.6 | 4.5 | PASS | 41.4 | Door-sensor + ARD battery PM visit |
| LIFT-02 | 4 | 91.2 | 3.9 | 3.0 | PASS | 53.9 | Door-sensor + ARD battery PM visit |
| LIFT-03 | 2 | 182.5 | 1.3 | 1.3 | PASS | 25.9 | Monitor |
| LIFT-04 | 5 | 73.0 | 2.9 | 3.1 | PASS | 64.3 | Door-sensor + ARD battery PM visit |


## 6. Load utilisation & change-of-use flags (IS 875-2)

| zone | area_sqm | DL | LL_design | LL_actual | total_MN | util_pct | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ground | 1630.53 | 7.5 | 4.0 | 3.84 | 18.49 | 96.0 | PASS |
| First | 1349.45 | 7.5 | 3.0 | 2.88 | 14.01 | 96.0 | PASS |
| Second | 1299.69 | 7.5 | 3.0 | 2.88 | 13.49 | 96.0 | PASS |
| Third | 1299.69 | 7.5 | 3.0 | 2.88 | 13.49 | 96.0 | PASS |
| Fourth | 1299.69 | 7.5 | 3.0 | 2.88 | 13.49 | 96.0 | PASS |
| Fifth | 1299.69 | 7.5 | 3.0 | 2.88 | 13.49 | 96.0 | PASS |
| Sixth | 1299.69 | 7.5 | 3.0 | 2.88 | 13.49 | 96.0 | PASS |
| Terrace + solar ballast 0.6 | 1299.69 | 7.5 | 1.5 | 0.6 | 10.53 | 40.0 | PASS-headroom 0.9 |
| Sports rm -> book bank | 179.3 | 7.5 | 4.0 | 5.0 | 2.24 | 125.0 | FLAG-structural check |


## 7. Water leakage ROI (IS 1172)

| metric | value |
| --- | --- |
| measured_lpcd | 201.2 |
| excess_lpcd | 66.2 |
| wasted_kl_per_yr | 11607.0 |
| wasted_rs_per_yr | 522315.0 |
| capex_rs | 85000.0 |
| annual_saving_rs | 78347.0 |
| payback_months | 13.0 |


## 8. Sixth-floor thermal / cool-roof case

| metric | value |
| --- | --- |
| sixth_floor_thermal_score | 2.36 |
| cool_roof_capex_rs | 86400.0 |
| annual_energy_saving_rs | 8640.0 |
| energy_only_payback_yr | 10.0 |


## 9. Preventive-maintenance compliance gaps

| asset | frequency | last_done | next_due | compliance_pct |
| --- | --- | --- | --- | --- |
| Exhaust fans | Quarterly | 2026-09-25 | 2026-12-25 | 84 |
| DG changeover test | Monthly | 2026-10-28 | 2026-11-28 | 88 |


## 10. Post-occupancy evaluation means (cleaned sample)

| index | mean_score |
| --- | --- |
| thermal_comfort | 3.38 |
| acoustic_privacy | 3.37 |
| water_supply | 3.07 |
| wifi_satisfaction | 3.41 |
| lan_reliability | 4.0 |
| safety_feeling | 3.99 |
| overall_satisfaction | 3.51 |

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
