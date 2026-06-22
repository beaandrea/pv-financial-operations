# Phase 1: Data Quality Triage & Issue Log

**Project:** Prescott & Vance Financial - Operations Capacity & Throughput Optimizer  
**Dataset:** 2024-2025 Global Retail Banking Operations Extract (500,000 records)  
**Objective:** To perform an initial data audit on the raw HRIS and operations extract prior to pipeline engineering, isolating solvable structural issues from unsolvable anomalies.

### Executive Summary
Initial exploratory data analysis using Python (Pandas) revealed a dataset with a 259.4 MB memory footprint, primarily due to timestamps loading as unstructured strings. The data clearly captures a massive 10% open backlog (50,000 unresolved cases). Notable solvable issues include legacy system entity fragmentation (misspelled hubs) and a specific system glitch causing negative processing times. 

**Strategic Analytical Signals:** 
* **SLA Distortion:** Text corruption artificially distorts SLA metrics. The clean `New York` hub has a 0% SLA breach rate, but the typo `NewYork` shows a 41% breach rate because overwhelmed Manila/London cases were mislabeled. 
* **YoY Degradation:** Initial grouping confirms Victoria Sterling's hypothesis: Merchant Dispute processing times in overloaded hubs surged by ~24% from 2024 to 2025.

---

### Issue Log

| Table | Column | Issue | Row Count | Magnitude | Solvable? | Resolution Plan |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `raw_pv_operations` | All Timestamps | **Data Type Inefficiency:** Loaded as `object` (string) rather than datetime, inflating memory usage. | 500,000 | High | Yes | Force standardization via Pandas `to_datetime()` to establish uniform ISO formats and enable date math. |
| `raw_pv_operations` | `Processing_Hub` | **Entity Fragmentation:** Legacy system naming inconsistencies (e.g., 'MNL', 'manila', 'Ph-Manila'). *Strategic Note: This text corruption artificially skews the SLA breach rates of the fragments.* | 25,000 | High | Yes | Implement a Python dictionary mapping to standardize all fragmented text strings into unified Parent Hubs (Manila, London, New York). |
| `raw_pv_operations` | `Resolution_Timestamp` | **Business Logic Violation:** Negative processing times detected in resolved cases. The resolution timestamp occurs *before* the intake timestamp, indicating a legacy system glitch. | 8,956 | Medium | Yes | Recalculate `Actual_Processing_Days` fresh from clean timestamps `(Resolution_Timestamp - Intake_Timestamp).dt.days`, then **drop** rows where the result is `< 0`. These represent genuine data corruption (1.8% of resolved cases) and dropping them preserves AHT accuracy without meaningful impact on aggregate throughput. |
| `raw_pv_operations` | `Dispute_Type` | **Missing Core Dimension:** Null values detected in the transaction category field. | 5,000 | Low | Yes | Drop rows. Representing exactly 1.0% of the dataset, dropping preserves aggregate analytical accuracy without forcing artificial 'Unknown' allocations. |
| `raw_pv_operations` | `Processing_Cost_USD` | **Missing Financial Data:** Cascading nulls caused by the missing `Dispute_Type` inputs above. | 5,000 | Low | Yes | Dropping the null `Dispute_Type` rows will natively resolve these trailing financial nulls. |
| `raw_pv_operations` | `Actual_Processing_Days` | **Expected Nulls (Backlog):** Nulls present due to open cases lacking a resolution date. | 50,000 | High | No | **Do not drop.** These represent the 10% active backlog. Quarantine these cases when calculating AHT, but include them when calculating total throughput volume. |