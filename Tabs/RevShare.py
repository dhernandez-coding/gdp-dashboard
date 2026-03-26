import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import datetime
import numpy as np
import json


# ✅ Load Data Function
def format_as_money(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "")
    return df

def load_data():
    """Load datasets from the /data folder and preprocess dates."""
    data_path = Path(__file__).parents[1] / "data"

    # Load CSVs
    revshare = pd.read_csv(data_path / "RevShareNewLogic.csv")
    revshare["RevShareDate"] = pd.to_datetime(revshare["RevShareDate"], errors="coerce")
    TETypeI= pd.read_csv(data_path / "vwTimeEntriesType1.csv")
    TETypeI["TimeEntryDate"] = pd.to_datetime(TETypeI["TimeEntryDate"], errors="coerce")
    TETypeII= pd.read_csv(data_path / "vwTimeEntriesType2.csv")
    TETypeII["TimeEntryDate"] = pd.to_datetime(TETypeII["TimeEntryDate"], errors="coerce")
    TETypeIII= pd.read_csv(data_path / "vwTimeEntriesType3.csv")
    TETypeIII["TimeEntryDate"] = pd.to_datetime(TETypeIII["TimeEntryDate"], errors="coerce")
    return revshare, TETypeI, TETypeII, TETypeIII

revshare, TETypeI,TETypeII,TETypeIII =load_data()




def run_revshare(start_date, end_date, revshare=revshare, TETypeI=TETypeI, TETypeII=TETypeII, TETypeIII=TETypeIII):
    st.title("Revenue Share Review")
    st.caption("v2.1 - Enhanced Table Formatting")
    custom_staff_list = st.session_state["custom_staff_list"]
    # Retrieve user role/permissions
    staff_code = st.session_state.get("staff_code", "")
    allowed_tabs = st.session_state.get("allowed_tabs", [])

    # Identify if user is admin (based on specific staff codes or admin role)
    # RAW = Russell, DLB = Donna. You can also check if "Settings" is in allowed_tabs as a proxy for admin.
    is_admin = (staff_code in ["RAW", "DLB", "admin"]) or ("Settings" in allowed_tabs)

    # Set up top KPIs with placeholders
    col1, col2, col3 = st.columns(3)
    kpi_revenue = col1.empty()
    kpi_hours = col2.empty()
    kpi_share = col3.empty()


    st.markdown("---")

    #  Step 1: Staff dropdown logic
    if is_admin:
        # Admins see everyone
        staff_selected = st.selectbox("Select Staff", custom_staff_list)
    else:
        # Restrict to their own code
        # If their staff_code is not in the list (e.g. data missing), default to it anyway or handle error
        if staff_code in custom_staff_list:
            # We can show a disabled selectbox or just a markdown
            # st.markdown(f"**Viewing data for:** {staff_code}")
            staff_selected = st.selectbox("Select Staff", [staff_code], disabled=True)
        else:
            st.error(f"Staff code '{staff_code}' not found in configuration.")
            st.stop()


    # Step 2: Filter and RevShare table
    filtered_rev = (
        revshare[
            (revshare["RevShareDate"] >= pd.to_datetime(start_date)) &
            (revshare["RevShareDate"] <= pd.to_datetime(end_date)) &
            (revshare["Staff"] == staff_selected)
        ]
        .drop(columns=[col for col in revshare.columns if col.startswith("Unnamed")])
        .sort_values("RevShareDate")
    )

    # Calculate new columns
    filtered_rev["Flat Fee Hours"] = filtered_rev["FONEHours"] + filtered_rev["FMONHours"]
    filtered_rev["Flat Fee Revenue"] = filtered_rev["FONERevenue"] + filtered_rev["FMONRevenue"]
    filtered_rev["Threshold"] = 14000.0
    filtered_rev["Eligible for Revenue Share"] = (filtered_rev["TotalRevShareMonth"] - filtered_rev["Threshold"]).clip(lower=0)


    # Rename columns
    filtered_rev = filtered_rev.rename(columns={
        "RevShareMonth": "Month",
        "RevShareYear": "Year",
        "RevShareDate": "Date",
        "AverageRate": "Average Collection Rate",
        "HourlyHours": "Hourly Hours Collected",
        "HourlyRevenue": "Hourly Revenue",
        "TotalRevShareMonth": "Total Production Revenue",
        "RevTier1": "Tier 1 Share",
        "RevTier2": "Tier 2 Share",
        "RevTier3": "Tier 3 Share",
        "RevTierTotal": "Production Revenue Share",
        "OriginationFees": "Origination Revenue Share",
        "RevShareTotal": "Total Revenue Share"
    })
    
    # Step 4: Reorder columns explicitly
    desired_order = [
        "Staff",
        "Month", # Or Date if prefer full date
        # "Date", 
        "Flat Fee Hours",
        "Average Collection Rate",
        "Flat Fee Revenue",
        "Hourly Hours Collected",
        "Hourly Revenue",
        "Total Production Revenue",
        "Threshold",
        "Eligible for Revenue Share",
        "Tier 1 Share",
        "Tier 2 Share",
        "Tier 3 Share",
        "Production Revenue Share",
        "Origination Revenue Share",
        "Total Revenue Share"
    ]

    # Use Date for display in Month column if needed, or just keep Month as digit. 
    # Use "Date" column content for "Month" column display if desired to match screenshot (10/01/2023)
    # The user screenshot shows "Month" with values like "10/01/2023".
    # Lets copy Date to Month or just use Date column renamed.
    # The rename above maps "RevShareMonth" to "Month" which is just the integer. 
    # Let's map "Date" to "Month" for the display.
    filtered_rev["Month"] = filtered_rev["Date"].dt.strftime("%m/%d/%Y")

    # Ensure all desired columns are in filtered_rev
    filtered_rev = filtered_rev[[col for col in desired_order if col in filtered_rev.columns]]
    
    # Format Money
    money_cols = [
        "Average Collection Rate",
        "Flat Fee Revenue",
        "Hourly Revenue",
        "Total Production Revenue",
        "Threshold",
        "Eligible for Revenue Share",
        "Tier 1 Share",
        "Tier 2 Share",
        "Tier 3 Share",
        "Production Revenue Share",
        "Origination Revenue Share",
        "Total Revenue Share"
    ]
    display_rev = format_as_money(filtered_rev.copy(), money_cols)
    
    st.subheader(f"Revenue Share Summary:")
    st.dataframe(display_rev, use_container_width=True, height=250) 
    
    total_share_val = filtered_rev["Total Revenue Share"].sum()
    st.subheader(f"Total Share: ${total_share_val:,.2f}")

    #  Step 5: Define reusable settings for FONE, FMON and Hourly
    col_renames = {
        "TimeEntryName": "Time Entry Name",
        "TimeEntryDate": "Date",
        "TimeEntryQuarter": "Quarter",
        "TimeEntryYear": "Year",
        "TimeEntryAmount": "Amount",
        "TimeEntryRate": "Rate",
        "TimeEntryGross": "Gross",
        "TimeEntryBilledAmount": "Billed Amount",
        # "TotalPaymentPayable": "Payable",
        # "TimeEntryBreakDown": "Breakdown",
        "TotalPayout": "Total Payout"
    }
    selected_cols = list(col_renames.values())

    # Step 4: Loop over each Time Entry type (HIDDEN FOR NOW)
    # Mapping from internal labels to user-friendly names
    label_map = {
        "Type I": "FONE",
        "Type II": "FMON",
        "Type III": "Hourly"
    }

    entry_datasets = [TETypeI, TETypeII, TETypeIII]
    entry_labels = ["Type I", "Type II", "Type III"]
    summary_frames = []

    for df, label in zip(entry_datasets, entry_labels):
        # Filter and rename
        filtered_te = (
            df[
                (df["TimeEntryDate"] >= pd.to_datetime(start_date)) &
                (df["TimeEntryDate"] <= pd.to_datetime(end_date)) &
                (df["Staff"] == staff_selected)
            ]
            .copy()
            .rename(columns=col_renames)
        )

        # Keep only relevant columns
        filtered_te = filtered_te[selected_cols]
        # display_te = format_as_money(filtered_te.copy(), ["Rate", "Gross", "Billed Amount", "Total Payout"])
        # Display - HIDDEN
        friendly_label = label_map[label]
        # st.subheader(f"{friendly_label} Time Entries")
        # st.dataframe(display_te, use_container_width=True, height=300)

        # Add for summary plot
        if not filtered_te.empty:
            filtered_te["Type"] = friendly_label  # ✅ Assign before selecting
            summary_frames.append(filtered_te[["Date", "Total Payout", "Type", "Amount"]])

    # 🧠 Step 5: Combine all for one summary plot
    if summary_frames:
        combined_summary = pd.concat(summary_frames)
        combined_summary = combined_summary.dropna(subset=["Total Payout"])
    
        ## ✅ Convert to monthly period and format to proper month string (e.g., "Jan 2025")
        combined_summary["Month"] = combined_summary["Date"].dt.to_period("M").dt.strftime("%b %Y")

        # ✅ Group by Month and Type
        payout_by_month = (
            combined_summary.groupby(["Month", "Type"], as_index=False)["Total Payout"].sum()
        )
 
        # ✅ Sort months chronologically (important to avoid random bar order)
        payout_by_month["Month_dt"] = pd.to_datetime(payout_by_month["Month"])
        payout_by_month = payout_by_month.sort_values("Month_dt")


        # 🎯 Fill the KPI placeholders now
        total_revenue_share = filtered_rev["Total Revenue Share"].sum()
        total_revenue = filtered_rev["Total Production Revenue"].sum()
        Amount = combined_summary["Amount"].sum()

        kpi_revenue.metric("Total Production Revenue", f"${total_revenue:,.0f}")
        kpi_hours.metric("Total Hours", f"{Amount:,.0f} hours")
        kpi_share.metric("Total Revenue Share", f"${total_revenue_share:,.0f}")

        # Plot
        st.subheader(f"Payout Summary for {staff_selected}")
        fig = px.bar(
            payout_by_month,
            x="Month",  # Still use string label
            y="Total Payout",
            color="Type",
            barmode="group",
            title="Monthly Total Payouts by Type of Time Entry"
        )
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Total Payout ($)",
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig, use_container_width=True)