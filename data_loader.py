import pandas as pd
from pathlib import Path
import streamlit as st

@st.cache_data(ttl=0)
def load_data():
    data_path = Path(__file__).parent / "data"

    # Load with no dtype forcing — let pandas infer
    revenue = pd.read_csv(data_path / "RevShareNewLogic.csv", encoding="utf-8")
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", encoding="utf-8")
    matters = pd.read_csv(data_path / "vMatters.csv", encoding="utf-8")

    # --- Parse dates first ---
    revenue["RevShareDate"] = pd.to_datetime(revenue["RevShareDate"], errors="coerce")
    billable_hours["BillableHoursDate"] = pd.to_datetime(billable_hours["BillableHoursDate"], errors="coerce")
    matters["MatterCreationDate"] = pd.to_datetime(matters["MatterCreationDate"], errors="coerce")

    # --- Define numeric cleaning (excluding date columns) ---
    def clean_numeric(df: pd.DataFrame, exclude_cols=None) -> pd.DataFrame:
        exclude_cols = exclude_cols or []
        for col in df.columns:
            if col in exclude_cols:
                continue
            
            # Skip columns that are clearly not numeric
            if df[col].dtype == "datetime64[ns]" or df[col].dtype.name.startswith("datetime"):
                continue
            if df[col].astype(str).str.contains("[A-Za-z]").any():
                # has letters → treat as text, skip cleaning
                continue
            
            if df[col].dtype == object:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(r"[\$,()]", "", regex=True)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                )
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                except Exception:
                    pass
                
        return df

    revenue = clean_numeric(revenue, exclude_cols=["RevShareDate"])
    billable_hours = clean_numeric(billable_hours, exclude_cols=["BillableHoursDate"])
    matters = clean_numeric(matters, exclude_cols=["MatterCreationDate"])

    # --- Drop rows with invalid dates ---
    revenue = revenue.dropna(subset=["RevShareDate"])
    billable_hours = billable_hours.dropna(subset=["BillableHoursDate"])
    matters = matters.dropna(subset=["MatterCreationDate"])

    # --- Derived date features ---
    billable_hours["Month"] = billable_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    billable_hours["Week"] = billable_hours["BillableHoursDate"] - pd.to_timedelta(
        billable_hours["BillableHoursDate"].dt.dayofweek, unit="D"
    )

    revenue["MonthDate"] = revenue["RevShareDate"].dt.to_period("M").dt.to_timestamp()
    revenue["WeekDate"] = revenue["RevShareDate"] - pd.to_timedelta(revenue["RevShareDate"].dt.dayofweek, unit="D")
    revenue["Month"] = revenue["RevShareDate"].dt.to_period("M").astype(str)
    revenue["Week"] = revenue["RevShareDate"] - pd.to_timedelta(revenue["RevShareDate"].dt.dayofweek, unit="D")

    matters["Week"] = matters["MatterCreationDate"] - pd.to_timedelta(
        matters["MatterCreationDate"].dt.dayofweek, unit="D"
    )

    # --- Modification timestamp tracking ---
    csv_files = [
        data_path / "RevShareNewLogic.csv",
        data_path / "vBillableHoursStaff.csv",
        data_path / "vMatters.csv",
    ]
    mtime_key = tuple(f.stat().st_mtime for f in csv_files)

    return revenue, billable_hours, matters, mtime_key
