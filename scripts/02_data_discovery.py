import pandas as pd
import os

print("--- P&V Financial: Data Discovery Pipeline ---")

file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_pv_operations.csv')
df = pd.read_csv(file_path)

print(f"\nDataset loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")

# Step 1: Data Types (BEFORE any conversion)
print("\n1. RAW DATA TYPES:")
print(df.dtypes)
print(f"\nMemory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Step 2: Missing Values
print("\n2. MISSING VALUES (NULLS):")
null_counts = df.isnull().sum()
print(null_counts[null_counts > 0])

# Step 3: Duplicates
print(f"\n3. DUPLICATE ROWS: {df.duplicated().sum()}")

# Step 4: Hub Name Variants
print("\n4. DISTINCT HUB NAMES (with counts):")
print(df['Processing_Hub'].value_counts(dropna=False))

# Step 5: Dispute Type Variants
print("\n5. DISTINCT DISPUTE TYPES (with counts):")
print(df['Dispute_Type'].value_counts(dropna=False))

# Step 6: Convert timestamps for further checks
df['Intake_Timestamp'] = pd.to_datetime(df['Intake_Timestamp'])
df['Resolution_Timestamp'] = pd.to_datetime(df['Resolution_Timestamp'])

# Step 7: Negative time check (resolved cases only)
resolved_mask = df['Resolution_Timestamp'].notna()
negative_time_mask = (
    df.loc[resolved_mask, 'Resolution_Timestamp'] < 
    df.loc[resolved_mask, 'Intake_Timestamp']
)
print(f"\n6. BUSINESS LOGIC VIOLATIONS:")
print(f"   Negative processing times (resolved cases): {negative_time_mask.sum():,} rows")
print(f"   Open cases (no resolution yet): {(~resolved_mask).sum():,} rows")

# Step 8: Numeric column statistics
print("\n7. NUMERIC COLUMN STATISTICS:")
numeric_cols = ['Actual_Processing_Days', 'SLA_Target_Days', 'Processing_Cost_USD']
print(df[numeric_cols].describe().round(2))

print("\n8. PROCESSING DAYS OUTLIER CHECK:")
print(f"   Min: {df['Actual_Processing_Days'].min()}")
print(f"   Max: {df['Actual_Processing_Days'].max()}")
print(f"   Values > 90 days: {(df['Actual_Processing_Days'] > 90).sum():,}")

# Step 9: SLA Status sanity check
print("\n9. SLA STATUS DISTRIBUTION:")
print(df['SLA_Status'].value_counts())

print("\n10. SLA BREACH RATE BY HUB (resolved cases only):")
resolved_df = df[df['SLA_Status'] != 'Open']
print(resolved_df.groupby('Processing_Hub')['SLA_Status']
      .apply(lambda x: f"{(x == 'Breached').sum() / len(x) * 100:.1f}%"))

print("\n11. SLA BREACH RATE BY DISPUTE TYPE (resolved cases only):")
print(resolved_df.groupby('Dispute_Type')['SLA_Status']
      .apply(lambda x: f"{(x == 'Breached').sum() / len(x) * 100:.1f}%"))

print("\n--- Discovery Complete ---")