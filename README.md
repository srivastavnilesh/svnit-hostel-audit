<p align="center">
  <img src="https://img.shields.io/badge/Status-Production_Ready-2EC4B6?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Tableau-Interactive-FF9F1C?style=for-the-badge&logo=tableau&logoColor=white" />
  <img src="https://img.shields.io/badge/Civil_Engineering-NextGen-E71D36?style=for-the-badge" />
</p>

<h1 align="center">🏗️ Digital Twin & Algorithmic Audit Engine</h1>
<p align="center"><b>Atal Bihari Bajpayee Bhavan | 500-Seater EWS Hostel, SVNIT Surat</b></p>

<p align="center">
  <a href="[https://public.tableau.com/app/profile/YOUR_PROFILE/viz/YOUR_VIZ_NAME/Dashboard](https://public.tableau.com/views/BoysHostelBuildingPerformanceReport/HostelBuildingPerformance?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)">
    <img src="https://img.shields.io/badge/🚀_Launch_Live_Dashboard-Click_Here-2EC4B6?style=for-the-badge" />
  </a>
</p>

<p align="center">
  <img src="dashboard_demo.gif" width="100%" alt="Interactive Dashboard Demo" />
  <br><i>Hover over the Floor Health chart to see the Viz-in-Tooltip magic. Click the link above to interact live.</i>
</p>

---

## 🧭 Quick Navigation
- [📊 Executive Summary](#-executive-summary)
- [🏛️ Statutory Anchors](#-statutory--code-anchors)
- [⚙️ System Architecture](#️-system-architecture)
---

## 📊 Executive Summary
Traditional facility audits rely on clipboards. I built an **Algorithmic Digital Twin** that replaces manual checks with a seeded, physics-aware data engine. It doesn't just find problems—it quantifies the exact ROI of fixing them.

| Metric | Value | Impact |
| :--- | :--- | :--- |
| **Building Health Index** | **83.9 / 100** | Governance-capped from 'A' due to lapsed Fire NOC |
| **Water Leakage** | **201 LPCD** | Wasting ₹5.2L/yr. Aerator ROI payback: **13 months** |
| **Lift Wait Time** | **75s (Observed)** | EN 81-20 proves capacity is ample (21.2%). Root cause: Operational misuse. |
| **Terrace Health** | **40 / 100** | Rectified at **₹0 Capex** by leveraging CPWD Cl. 7.1.3 10-yr WP bond. |

---

## 🏛️ Statutory & Code Anchors
<details>
<summary>📜 <b>Click to expand full compliance register</b></summary>

- **Structural:** IS 13311-1 (UPV), IS 456 (Crack limits), IS 875-2 (Live loads)
- **Fire & Governance:** SMC Fire NOC 2023-24/1108 (42 conditions), NBC 2016
- **MEP & Traffic:** EN 81-20 (Lift traffic), IS 1172 (Water supply), CPWD Lift Eligibility (≤8h minor downtime)
- **CPWD NIT:** 07/EE(C)-Surat/SE-Vadodara/ADG(RM)/2020-21 (BOQ & Guarantee Bonds)

</details>

---

## ⚙️ System Architecture

```mermaid
graph TD
    A[Raw BOQ & Drawings] -->|Python ETL| B(Seeded Digital Twin DB)
    B --> C{Audit Engine}
    C -->|IS 13311/456| D[Structural Scoring]
    C -->|SMC NOC 42| E[Fire Compliance]
    C -->|EN 81-20| F[Lift Traffic]
    D & E & F --> G[Building Health Index]
    G --> H[Tableau Command Center]
    G --> I[MS Project Gantt]
