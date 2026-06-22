import pandas as pd
import numpy as np
import os

print("--- P&V Financial: Data Cleaning & Augmentation Pipeline ---")

# Load the raw data
input_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_pv_operations.csv')
df = pd.read_csv(input_path)
initial_rows = len(df)
print(f"Loaded raw dataset: {initial_rows:,} rows.")

# Step 1: Execute Issue Log Resolutions
# Resolution 1: Standardize Timestamps
print("Standardizing timestamps...")
df['Intake_Timestamp'] = pd.to_datetime(df['Intake_Timestamp'])
df['Resolution_Timestamp'] = pd.to_datetime(df['Resolution_Timestamp'])

# Resolution 2: Clean Entity Fragmentation & Relational Integrity
print("Restoring Hub integrity using Agent IDs as the Source of Truth...")
# Instead of mapping messy text, I will extract the true location directly from the agent prefix
df['Processing_Hub'] = np.select(
    [df['Processing_Agent'].str.startswith('MNL', na=False),
     df['Processing_Agent'].str.startswith('LND', na=False),
     df['Processing_Agent'].str.startswith('NY', na=False)],
    ['Manila', 'London', 'New York'],
    default=df['Processing_Hub'] # Fallback (though won't be needed here)
)

# Resolution 3: Drop Missing Core Dimensions (Cascades to fix missing costs)
print("Dropping null Dispute Types...")
df = df.dropna(subset=['Dispute_Type'])

# Resolution 4: Fix Business Logic Violations (Negative Time Glitch)
print("Recalculating processing days and dropping legacy glitches...")
resolved_mask = df['Resolution_Timestamp'].notna()
df.loc[resolved_mask, 'Actual_Processing_Days'] = (
    df.loc[resolved_mask, 'Resolution_Timestamp'] - df.loc[resolved_mask, 'Intake_Timestamp']
).dt.days

# Drop the negative time glitches (leaving the open NaT cases intact)
negative_mask = (df['Actual_Processing_Days'] < 0) & resolved_mask
df = df[~negative_mask]

# Step 2: Augment the Data
print("Augmenting data with new analytical metrics...")

# Metric 1: Exact variance from SLA (Positive = Days Late, Negative = Days Early)
# Note: Open cases (Actual_Processing_Days = NaN) will produce NaN here by design.
# These are quarantined at the analysis layer, not dropped here.
df['Days_vs_SLA_Target'] = df['Actual_Processing_Days'] - df['SLA_Target_Days']

# Metric 2: Processing Speed Category for Tableau filtering
# Upper bin expanded to 365 to safely catch severe Merchant Dispute outliers
df['Speed_Category'] = pd.cut(
    df['Actual_Processing_Days'], 
    bins=[0, 7, 14, 30, 365], 
    labels=['Lightning (0-7d)', 'Standard (8-14d)', 'Delayed (15-30d)', 'Severe Backlog (30d+)']
) # Bins are left-exclusive: minimum value from generator is 1 day, so no cases fall below bin floor

# !!! VALIDATION CHECK !!!
print("\n--- Validation ---")
print("Hub distribution after cleaning:")
print(df['Processing_Hub'].value_counts())
print(f"\nSLA Status distribution:")
print(df['SLA_Status'].value_counts())
print(f"\nNull check on augmented columns (NaNs expected for Open/backlog cases only):")
print(df[['Days_vs_SLA_Target', 'Speed_Category']].isnull().sum())

# Step 3: Export fact table
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

# Table A: Historical Operations (Resolved Cases Only)
resolved_fact = df[df['SLA_Status'] != 'Open']
resolved_path = os.path.join(output_dir, 'fact_pv_operations.csv')
resolved_fact.to_csv(resolved_path, index=False)

# Table B: Open Backlog Queue (Active Cases)
open_backlog = df[df['SLA_Status'] == 'Open']
backlog_path = os.path.join(output_dir, 'fact_pv_backlog.csv')
open_backlog.to_csv(backlog_path, index=False)

final_rows = len(df)
rows_dropped = initial_rows - final_rows

print(f"\n--- Pipeline Complete ---")
print(f"Rows Dropped: {rows_dropped:,} ({(rows_dropped/initial_rows)*100:.1f}%)")
print(f"Resolved Operations exported: {len(resolved_fact):,} rows -> {resolved_path}")
print(f"Open Backlog exported: {len(open_backlog):,} rows -> {backlog_path}")