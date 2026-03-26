
import pandas as pd
import sys
from pathlib import Path
# Mocking streamlit to avoid import errors in data_loader
from unittest.mock import MagicMock
mock_st = MagicMock()
mock_st.cache_data = lambda f=None, **kwargs: f if f else lambda x: x
sys.modules["streamlit"] = mock_st

# Manually load data_loader
sys.path.append(str(Path.cwd()))
from data_loader import load_data

def test_flat_matter_logic():
    print("Loading data...")
    revenue, billable_hours, matters, flat_matters, mtime_key = load_data()
    
    print(f"Loaded {len(flat_matters)} flat matters.")
    
    # Simulate logic
    ESTIMATED_RATE = 250.0 # Placeholder
    
    # 1. Group hours by Matter
    # Assuming 'MatterName' links them.
    # billable_hours columns: BillableHoursAmount, StaffAbbreviation, BillableHoursDate, MatterName
    
    matter_hours = billable_hours.groupby('MatterName')['BillableHoursAmount'].sum().reset_index()
    matter_hours.rename(columns={'BillableHoursAmount': 'TotalHours'}, inplace=True)
    
    # 2. Merge with Flat Matters
    # flat_matters columns: MatterTypeID, MatterSourceID, MatterName, LastInvoiceAmount
    merged = pd.merge(flat_matters, matter_hours, on='MatterName', how='left')
    
    # 3. Calculate Burn
    merged['TotalHours'] = merged['TotalHours'].fillna(0)
    merged['BurnedAmount'] = merged['TotalHours'] * ESTIMATED_RATE
    
    # 4. Filter
    # Ensure LastInvoiceAmount is numeric
    merged = merged[merged['LastInvoiceAmount'] > 0] 
    
    merged['PercentUsed'] = merged['BurnedAmount'] / merged['LastInvoiceAmount']
    
    at_risk = merged[merged['PercentUsed'] >= 0.8]
    
    print("\n--- At Risk Matters ---")
    if not at_risk.empty:
        print(at_risk[['MatterName', 'LastInvoiceAmount', 'TotalHours', 'BurnedAmount', 'PercentUsed']].head())
    else:
        print("No matters at risk found with current data/threshold.")

if __name__ == "__main__":
    test_flat_matter_logic()
