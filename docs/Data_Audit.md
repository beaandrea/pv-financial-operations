# Phase 1: Data Quality Triage & Issue Log

**Project:** Prescott & Vance Financial - Operations Capacity Optimizer  
**Dataset:** 2024-2025 Retail Banking Operations Extract (~500,000 records)  
**Objective:** To perform an initial data audit on the raw operations extract prior to pipeline engineering, isolating solvable structural issues from unsolvable legacy system anomalies.

### Executive Summary
Audit of 500,000+ raw records revealed three legacy system failures that would have invalidated all hub-level analysis if left unresolved. The most critical: ~25,000 geographic misassignments that required bypassing the corrupted text field entirely and reconstructing hub data from Agent_ID prefixes — a source-of-truth decision that became the foundation of the entire pipeline.

---

### Issue Log

| Table | Column | Issue | Row Count | Magnitude | Solvable? | Resolution Plan |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `raw_operations` | `Processing_Hub` | **Dimension Mismatch / Inconsistent Categorization:** Legacy text fields corrupted geographic placement (e.g., assigning "Manila" agents to "New York"). | ~25,000 | High | Yes | **Established Source of Truth:** Bypassed manual text mapping and engineered a Python pipeline step to extract the true geographic location directly from the `Agent_ID` prefix (`MNL`, `LND`, `NY`). |
| `raw_operations` | `Dispute_Type` | **Missing Core Dimension:** Null values detected in the primary ticket classification field. | ~5,000 | Low | Yes | Dropped rows. Representing 1% of the 500k dataset, dropping preserves aggregate SLA accuracy without introducing artificial 'Unknown' categories. |
| `raw_operations` | `Resolution_Timestamp` | **Business Logic Anomaly:** Negative values present where resolution dates occurred *before* intake dates. | ~10,000 | Medium | Yes | Identified as legacy system auto-close errors. Quarantined and filtered out instances where `Actual_Processing_Days < 0` to prevent skewed handling time averages. |

<br>

# Phase 2: Strategic SQL EDA & Business Insights

**Project:** Prescott & Vance Financial - Operations Capacity Optimizer  
**Dataset:** Cleaned `fact_pv_operations` table (SQLite Database) 
**Objective:** To execute business-focused EDA using SQL, testing competing stakeholder hypotheses (global understaffing vs. structural resource misallocation).

### Requirements Gathering
* **Stakeholder Goals:** Evaluate the Compliance Head's theory of universal understaffing against the COO's theory of idle capacity to guide headcount budget strategy. Compliance Head believed the issue was universal understaffing across all dispute types. COO suspected idle capacity in specific teams masked as a staffing shortage. The SQL analysis was designed to stress-test both hypotheses against breach rate and throughput data simultaneously.
* **Columns & Coverage:** Isolate `Dispute_Type` and `Processing_Hub` against the core performance metrics (`Actual_Processing_Days` and `SLA_Status`).

---

### Insights Log

| SQL Query Focus | Metric & Dimension | The Finding | Relevant Stakeholder | Domain Context (Why it matters) |
| :--- | :--- | :--- | :--- | :--- |
| **Aggregates** (SLA Breaches) | `Breach_Rate_Pct` by `Dispute_Type` | **Merchant Disputes are the sole crisis.** They fail SLAs at an 83.3% rate, while Identity Theft and Fraud sit near 0%. | Head of Compliance (Marcus) | Validates that customer complaints are spiking, but disproves the theory that *all* teams are running on empty. The crisis is localized. |
| **Notable Segments** (YoY Degradation) | `Avg_Days` YoY by `Processing_Hub` | **The 23% surge is isolated.** Average handling times in Manila and London jumped from 39.3 days (2024) to 48.7 days (2025). | COO (Victoria) | Mathematically validates the COO's observation of a 23.9% degradation, pinpointing exactly where the operational friction is occurring. |
| **Capacity Analysis** (True Velocity) | `Total_Volume` / `Agent_Count` by `Hub` | **New York has massive throughput superiority.** NY handles ~22,000 cases per agent (0% breach) vs Manila's ~14,000 cases per agent (47% breach). | COO (Victoria) | Proves that cross-training is not just a theory, but a mathematical certainty. NY agents process 50% more volume in a fraction of the time, proving no net-new headcount is required. |