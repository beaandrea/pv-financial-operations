import pandas as pd
import numpy as np
import os

print("Initializing Prescott & Vance Financial data generation...")

# Set random seed for reproducibility
np.random.seed(42)
NUM_ROWS = 500000

# Step 1: The Core Dimensions
dispute_types = ['Credit Card Fraud', 'Identity Theft', 'Unauthorized Transfer', 'Merchant Dispute']
hubs = ['New York', 'Manila', 'London']

hub_allocation = np.random.choice(hubs, NUM_ROWS, p=[0.15, 0.50, 0.35])
type_allocation = np.random.choice(dispute_types, NUM_ROWS, p=[0.3, 0.1, 0.2, 0.4])

df = pd.DataFrame({
    'Dispute_ID': ['DISP-' + str(i).zfill(7) for i in range(1, NUM_ROWS + 1)],
    'Dispute_Type': type_allocation,
    'Processing_Hub': hub_allocation
})

# Step 2: SLA Targets Based on Dispute Type
sla_mapping = {
    'Credit Card Fraud': 14,
    'Unauthorized Transfer': 14,
    'Identity Theft': 30,
    'Merchant Dispute': 30
}
df['SLA_Target_Days'] = df['Dispute_Type'].map(sla_mapping)

# Generate Timestamps spanning exactly 2 years (2024-01-01 to 2025-12-31)
start_date = pd.to_datetime('2024-01-01')
random_days = np.random.randint(0, 730, size=NUM_ROWS)
df['Intake_Timestamp'] = start_date + pd.to_timedelta(random_days, unit='D')

# Step 3: Team & Agent Capacity Mapping
manila_agents = [f'MNL-{str(i).zfill(3)}' for i in range(1, 16)]
london_agents = [f'LND-{str(i).zfill(3)}' for i in range(1, 16)]
ny_agents = [f'NY-{str(i).zfill(3)}' for i in range(1, 4)]

agent_col = np.empty(NUM_ROWS, dtype=object)
team_col = np.empty(NUM_ROWS, dtype=object)

manila_mask = df['Processing_Hub'] == 'Manila'
london_mask = df['Processing_Hub'] == 'London'
ny_mask = df['Processing_Hub'] == 'New York'

# Manila (Skewed to overload Team Charlie)
manila_probs = [0.05]*12 + [0.133, 0.133, 0.134]
manila_idx = np.where(manila_mask)[0]
manila_chosen = np.random.choice(manila_agents, size=len(manila_idx), p=manila_probs)
agent_col[manila_idx] = manila_chosen
team_col[manila_idx] = np.where(
    pd.Series(manila_chosen).isin(manila_agents[-3:]), 'Team Charlie',
    np.where(pd.Series(manila_chosen).isin(manila_agents[:6]), 'Team Alpha', 'Team Bravo')
)

# London
london_idx = np.where(london_mask)[0]
london_chosen = np.random.choice(london_agents, size=len(london_idx))
agent_col[london_idx] = london_chosen
team_col[london_idx] = np.where(
    pd.Series(london_chosen).isin(london_agents[:5]), 'Team Delta',
    np.where(pd.Series(london_chosen).isin(london_agents[5:10]), 'Team Echo', 'Team Foxtrot')
)

# New York
ny_idx = np.where(ny_mask)[0]
agent_col[ny_idx] = np.random.choice(ny_agents, size=len(ny_idx))
team_col[ny_idx] = 'Team Gulf'

df['Processing_Agent'] = agent_col
df['Processing_Team'] = team_col

# Step 4: Complexity Tiers
df['Complexity_Tier'] = np.select(
    [df['Dispute_Type'] == 'Credit Card Fraud',
     df['Dispute_Type'] == 'Identity Theft',
     df['Dispute_Type'] == 'Unauthorized Transfer',
     df['Dispute_Type'] == 'Merchant Dispute'],
    [np.random.choice(['Low', 'Medium', 'High'], size=NUM_ROWS, p=[0.2, 0.5, 0.3]),
     np.random.choice(['Low', 'Medium', 'High'], size=NUM_ROWS, p=[0.1, 0.3, 0.6]),
     np.random.choice(['Low', 'Medium', 'High'], size=NUM_ROWS, p=[0.3, 0.4, 0.3]),
     np.random.choice(['Low', 'Medium', 'High'], size=NUM_ROWS, p=[0.4, 0.4, 0.2])],
    default=np.random.choice(['Low', 'Medium', 'High'], size=NUM_ROWS, p=[0.33, 0.34, 0.33])
)

# Step 5: Cost Engineering
base_costs = {'Credit Card Fraud': 45, 'Identity Theft': 85, 'Unauthorized Transfer': 55, 'Merchant Dispute': 35}
complexity_multiplier = {'Low': 1.0, 'Medium': 1.4, 'High': 2.1}

df['Base_Cost'] = df['Dispute_Type'].map(base_costs)
df['Comp_Mult'] = df['Complexity_Tier'].map(complexity_multiplier)
random_variance = np.random.uniform(0.85, 1.15, size=NUM_ROWS)

df['Processing_Cost_USD'] = np.round(df['Base_Cost'] * df['Comp_Mult'] * random_variance, 2)

# Drop temporary calculation columns
df = df.drop(columns=['Base_Cost', 'Comp_Mult'])

# Step 6: Engineer the Resolution & YoY Insight
conditions = [
    df['Processing_Hub'] == 'New York',
    df['Dispute_Type'] == 'Merchant Dispute'
]
choices = [
    np.random.normal(loc=7, scale=2, size=NUM_ROWS),
    np.random.normal(loc=40, scale=5, size=NUM_ROWS)
]
default = np.random.normal(loc=12, scale=3, size=NUM_ROWS)

processing_days = np.select(conditions, choices, default=default)
df['Actual_Processing_Days'] = np.maximum(1, processing_days.astype(int))

# Apply the 23%+ YoY degradation for 2025 Merchant Disputes in overloaded hubs
is_2025 = df['Intake_Timestamp'].dt.year == 2025
is_merchant = df['Dispute_Type'] == 'Merchant Dispute'
is_overloaded_hub = df['Processing_Hub'].isin(['Manila', 'London'])

df.loc[is_2025 & is_merchant & is_overloaded_hub, 'Actual_Processing_Days'] = \
    (df.loc[is_2025 & is_merchant & is_overloaded_hub, 'Actual_Processing_Days'] * 1.25).astype(int)

df['Resolution_Timestamp'] = df['Intake_Timestamp'] + pd.to_timedelta(df['Actual_Processing_Days'], unit='D')

# Step 7: SLA Status & Open Cases
df['SLA_Status'] = np.where(df['Actual_Processing_Days'] <= df['SLA_Target_Days'], 'Met', 'Breached')

open_indices = np.random.choice(df.index, size=int(NUM_ROWS * 0.10), replace=False)
df.loc[open_indices, 'Resolution_Timestamp'] = pd.NaT
df.loc[open_indices, 'Actual_Processing_Days'] = np.nan
df.loc[open_indices, 'SLA_Status'] = 'Open'

# Step 8: Injecting the Mess
messy_hubs = ['MNL', 'manila', 'Ph-Manila', 'NY', 'NewYork', 'LND', 'london']
messy_indices = np.random.choice(df.index, size=int(NUM_ROWS * 0.05), replace=False)
df.loc[messy_indices, 'Processing_Hub'] = np.random.choice(messy_hubs, size=len(messy_indices))

# O(1) lookup using a Set for massive performance gain
open_indices_set = set(open_indices)
glitch_indices = np.random.choice(df.index, size=int(NUM_ROWS * 0.02), replace=False)
glitch_indices = np.array([idx for idx in glitch_indices if idx not in open_indices_set])

df.loc[glitch_indices, 'Resolution_Timestamp'] = df.loc[glitch_indices, 'Intake_Timestamp'] - pd.to_timedelta(np.random.randint(1, 15, size=len(glitch_indices)), unit='D')

null_indices = np.random.choice(df.index, size=int(NUM_ROWS * 0.01), replace=False)
df.loc[null_indices, 'Dispute_Type'] = np.nan
df.loc[null_indices, 'Processing_Cost_USD'] = np.nan # Ensure cost is null if type is unknown

# Step 9: Export to CSV
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'raw_pv_operations.csv')

df.to_csv(output_path, index=False)
print(f"Success! {NUM_ROWS:,} rows generated at {output_path}")
print(f"Dataset Shape: {df.shape}")