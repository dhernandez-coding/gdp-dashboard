import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import datetime

# ✅ Set default date range (One year ago to today)
today = pd.Timestamp.today()
default_start_date = today - pd.DateOffset(years=1)
default_end_date = today - pd.DateOffset(days=2)

# ✅ Define Colors
PRIMARY_COLOR = "#399db7"  # Light blue
DARK_BLUE = "#052b48"      # Dark blue
COMPLEMENTARY_COLOR1 = "#FF6F61"  # Coral (for differentiation)
COMPLEMENTARY_COLOR2 = "#F4A261"  # Warm orange (for better contrast)

# ✅ Set Streamlit Page Config
st.set_page_config(
    page_title="Time Entry Dashboard",
    page_icon="📊",
    layout="wide"
)

# ✅ Load Data Function
@st.cache_data(ttl=86400)  # Cache expires after 86400 seconds (24 hours)
def load_data():
    """Load datasets from the /data folder and preprocess dates."""
    data_path = Path(__file__).parent / "data"

    # Load CSVs
    revenue = pd.read_csv(data_path / "RevShareNewLogic.csv", parse_dates=["RevShareDate"])
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", parse_dates=["BillableHoursDate"])
    matters = pd.read_csv(data_path / "vMatters.csv", parse_dates=["MatterCreationDate"])

    # ✅ Apply Date Transformations Once (for efficiency)
    billable_hours["Month"] = billable_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    billable_hours["Week"] = billable_hours["BillableHoursDate"] - pd.to_timedelta(billable_hours["BillableHoursDate"].dt.dayofweek, unit="D")

    revenue["Month"] = revenue["RevShareDate"].dt.to_period("M").astype(str)
    revenue["Week"] = revenue["RevShareDate"] - pd.to_timedelta(revenue["RevShareDate"].dt.dayofweek, unit="D")

    matters["Week"] = matters["MatterCreationDate"] - pd.to_timedelta(matters["MatterCreationDate"].dt.dayofweek, unit="D")

    return revenue, billable_hours, matters

# Load data
revenue, billable_hours, matters = load_data()

# ✅ Predefined Staff List (Always Show These)
custom_staff_list = ["AEZ", "BPL", "CAJ", "JER", "JRJ", "RAW", "WMJ"]

# ----------------------------------------------------------------------------
# ✅ HEADER WITH COMPANY LOGO
header_bg_color = "#052b48"  # Dark blue background for header
st.markdown(
    f"""
    <div style="background-color:{header_bg_color}; padding:20px; text-align:center; border-radius:5px;">
        <h1 style="color:white; margin-bottom:5px;">Time Entry Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ----------------------------------------------------------------------------
# ✅ DATE FILTER
st.sidebar.header("Filter Data by Date")
min_date = min(revenue["RevShareDate"].min(), billable_hours["BillableHoursDate"].min(), matters["MatterCreationDate"].min())
if min_date < pd.Timestamp("2020-01-01"):
    min_date = pd.Timestamp("2020-01-01")
max_date = max(revenue["RevShareDate"].max(), billable_hours["BillableHoursDate"].max(), matters["MatterCreationDate"].max())

# Make sure default_start_date and default_end_date are within bounds
default_start_date = max(default_start_date, min_date)
default_end_date = min(default_end_date, max_date)

date_range = st.sidebar.date_input(
    "Select Date Range",
    [default_start_date, default_end_date],
    min_value=min_date,
    max_value=max_date
)

# Convert to Timestamp for filtering
start_date = pd.Timestamp(date_range[0])
end_date = pd.Timestamp(date_range[1])

# Apply date filter to all datasets
filtered_revenue = revenue[(revenue["RevShareDate"] >= start_date) & (revenue["RevShareDate"] <= end_date)]
filtered_team_hours = billable_hours[(billable_hours["BillableHoursDate"] >= start_date) & (billable_hours["BillableHoursDate"] <= end_date)]
filtered_matters = matters[(matters["MatterCreationDate"] >= start_date) & (matters["MatterCreationDate"] <= end_date)]
# ✅ Filter matters created within the selected year-to-date range
filtered_matters_ytd = filtered_matters[
    (filtered_matters["MatterCreationDate"] >= pd.Timestamp(start_date.year, 1, 1)) &
    (filtered_matters["MatterCreationDate"] <= end_date)
]

# ✅ Ensure Correct Column Naming (Rename StaffAbbreviation to Staff)
filtered_team_hours = filtered_team_hours.rename(columns={"StaffAbbreviation": "Staff"})
filtered_revenue = filtered_revenue.rename(columns={"StaffAbbreviation": "Staff"})

# ✅ Filter Data to Include Only Predefined Staff
filtered_team_hours = filtered_team_hours[filtered_team_hours["Staff"].isin(custom_staff_list)]
filtered_revenue = filtered_revenue[filtered_revenue["Staff"].isin(custom_staff_list)]

st.markdown("---")
# ----------------------------------------------------------------------------
## Transformating data 
# ✅ Convert Dates for Monthly Aggregation
filtered_revenue["Month"] = filtered_revenue["RevShareDate"].dt.to_period("M").astype(str)
filtered_team_hours["Month"] = filtered_team_hours["BillableHoursDate"].dt.to_period("M").astype(str)

# ✅ Convert Dates for Weekly Aggregation
filtered_revenue["Week"] = filtered_revenue["RevShareDate"] - pd.to_timedelta(filtered_revenue["RevShareDate"].dt.dayofweek, unit="D")
filtered_team_hours["Week"] = filtered_team_hours["BillableHoursDate"] - pd.to_timedelta(filtered_team_hours["BillableHoursDate"].dt.dayofweek, unit="D")

# ✅ Identify the Last Selected Month from Date Slider
last_selected_month = max(filtered_revenue["Month"])  # Last selected month

# ✅ 1️⃣ Revenue Per Staff (Monthly)
revenue_per_staff_monthly = filtered_revenue.groupby(["Month", "Staff"], as_index=False)["RevShareTotal"].sum()

# ✅ 2️⃣ Total Team Revenue (Monthly)
total_team_revenue_monthly = revenue_per_staff_monthly.groupby("Month", as_index=False)["RevShareTotal"].sum()

# ✅ 3️⃣ Billable Hours Per Staff (Weekly)
billable_hours_per_staff_weekly = filtered_team_hours.groupby(["Week", "Staff"], as_index=False)["BillableHoursAmount"].sum()

# ✅ 4️⃣ Billable Hours Per Staff (Monthly)
billable_hours_per_staff_monthly = filtered_team_hours.groupby(["Month", "Staff"], as_index=False)["BillableHoursAmount"].sum()

# ✅ 5️⃣ Total Team Billable Hours (Weekly)
total_team_hours_weekly = billable_hours_per_staff_weekly.groupby("Week", as_index=False)["BillableHoursAmount"].sum()

# ✅ 6️⃣ Total Team Billable Hours (Monthly)
total_team_hours_monthly = billable_hours_per_staff_monthly.groupby("Month", as_index=False)["BillableHoursAmount"].sum()
# ✅ Convert MatterCreationDate to Weekly Period
filtered_matters_ytd["Week"] = filtered_matters_ytd["MatterCreationDate"] - pd.to_timedelta(filtered_matters_ytd["MatterCreationDate"].dt.dayofweek, unit="D")

# ----------------------------------------------------------------------------
# ✅ KPI METRICS (Dynamically Updating)
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${filtered_revenue['RevShareTotal'].sum():,.0f}")
col2.metric("Total Team Hours", f"{filtered_team_hours['BillableHoursAmount'].sum():,.0f} hours")
col3.metric("Total Matters", f"{filtered_matters.shape[0]:,.0f} matters")

st.markdown("---")

# ----------------------------------------------------------------------------
# ✅ WEEKLY TEAM HOURS & YTD REVENUE CHARTS
st.subheader("Weekly Team Hours & YTD Revenue", divider="gray")
col1, col2 = st.columns(2)
# Filter only prior months
prior_months_team_hours = total_team_hours_monthly[total_team_hours_monthly["Month"] < last_selected_month]
# ✅ Convert BillableHoursDate to Weekly Period & Aggregate
# 🎯 PLOT 1: Cumulative Revenue (Bar Chart)
with col1:
    # ✅ REVENUE PER STAFF (Bar Chart)


    fig1 = px.bar(
        filtered_revenue,
        x="Staff",
        y="RevShareTotal",
        color="Staff",
        title="Revenue per Staff",
        labels={"RevShareTotal": "Revenue ($)"},
        color_discrete_sequence=[PRIMARY_COLOR]
    )

    fig1.update_layout(xaxis_title="", yaxis_title="Revenue ($)", showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)



# 🎯 PLOT 2: prior_team_hours (Bar Chart)
with col2:

    fig_prior_team_hours = px.bar(
        prior_months_team_hours,  # ✅ Filtered dataset
        x="Month",
        y="BillableHoursAmount",
        title="Team Hours - Prior Months",
        labels={"Month": "Month", "BillableHoursAmount": "Hours Worked"},
        color_discrete_sequence=[DARK_BLUE]
    )

    fig_prior_team_hours.update_layout(
        xaxis_title="Month",
        yaxis_title="Hours Worked",
        xaxis=dict(tickmode="array", tickvals=prior_months_team_hours["Month"])
    )

    st.plotly_chart(fig_prior_team_hours, use_container_width=True)



# ----------------------------------------------------------------------------
# ✅ WEEKLY INDIVIDUAL HOURS (Grouped Bar Chart)
st.subheader("Weekly Individual Hours", divider="gray")

# ✅ Convert BillableHoursDate to Weekly Period & Aggregate
filtered_team_hours["Week"] = filtered_team_hours["BillableHoursDate"] - pd.to_timedelta(filtered_team_hours["BillableHoursDate"].dt.dayofweek, unit="D")

# ✅ Aggregate by Week and Staff
weekly_individual_hours = filtered_team_hours.groupby(["Week", "Staff"], as_index=False)["BillableHoursAmount"].sum()

# ✅ Compute Weekly Average Daily Hours (Total Weekly Hours / 5)
weekly_individual_hours["AvgDailyHours"] = weekly_individual_hours["BillableHoursAmount"] / 5

# ✅ Create Grouped Bar Chart with Enhanced Tooltip
fig_individual_hours_bar = px.bar(
    weekly_individual_hours,
    x="Week",
    y="BillableHoursAmount",
    color="Staff",
    title="Weekly Individual Hours Worked",
    labels={"BillableHoursAmount": "Total Hours Worked", "Week": "Week Start", "Staff": "Staff Member"},
    color_discrete_sequence=px.colors.qualitative.Set1,
    barmode="group",
    hover_data={"AvgDailyHours": ":.2f"}  # ✅ Show Avg Daily Hours in Tooltip (formatted to 2 decimals)
)

fig_individual_hours_bar.update_layout(
    xaxis_title="Week",
    yaxis_title="Total Hours Worked",
    xaxis=dict(tickformat="%Y-%m-%d"),  # ✅ Format weeks properly
)

# ✅ Display the Chart in Streamlit
st.plotly_chart(fig_individual_hours_bar, use_container_width=True)
# ----------------------------------------------------------------------------


col11, col22 = st.columns(2)

with col11:
    # Weekly Team Hours Chart
    fig_weekly_hours = px.bar(
    total_team_hours_weekly,  # ✅ Use the correct dataset
    x="Week",
    y="BillableHoursAmount",
    title="Weekly Team Hours",
    labels={"Week": "Week Start", "BillableHoursAmount": "Hours Worked"},
    color_discrete_sequence=[DARK_BLUE]
)

    fig_weekly_hours.update_layout(
    xaxis_title="Week",
    yaxis_title="Hours Worked",
    xaxis=dict(tickformat="%Y-%m-%d")  # Format dates for better readability
)
    st.plotly_chart(fig_weekly_hours, use_container_width=True)
      
with col22:
        
        fig_ytd_revenue = px.bar(
        total_team_revenue_monthly,  # ✅ Use the correct dataset
        x="Month",
        y="RevShareTotal",  # ✅ Ensure correct column is used for revenue
        title="YTD Revenue (Cumulative)",
        labels={"RevShareTotal": "Cumulative Revenue ($)", "Month": "Month"},
        color_discrete_sequence=[COMPLEMENTARY_COLOR1]
    )

        fig_ytd_revenue.update_layout(
        xaxis_title="Month",
        yaxis_title="Cumulative Revenue ($)",
        xaxis=dict(tickmode="array", tickvals=total_team_revenue_monthly["Month"]),
    )

        st.plotly_chart(fig_ytd_revenue, use_container_width=True)
# ✅ MONTHLY INDIVIDUAL HOURS (Grouped Bar Chart)
st.subheader("Monthly Individual Hours", divider="gray")

# ✅ Convert BillableHoursDate to Monthly Period & Aggregate
filtered_team_hours["Month"] = filtered_team_hours["BillableHoursDate"].dt.to_period("M").astype(str)
monthly_individual_hours = filtered_team_hours.groupby(["Month", "Staff"], as_index=False)["BillableHoursAmount"].sum()

fig_individual_hours_bar = px.bar(
    monthly_individual_hours,
    x="Month",
    y="BillableHoursAmount",
    color="Staff",
    title="Monthly Individual Hours Worked",
    labels={"BillableHoursAmount": "Total Hours Worked", "Month": "Month", "Staff": "Staff Member"},
    color_discrete_sequence=px.colors.qualitative.Set1,
    barmode="group"
)

fig_individual_hours_bar.update_layout(
    xaxis_title="Month",
    yaxis_title="Total Hours Worked",
    xaxis=dict(tickmode="array", tickvals=monthly_individual_hours["Month"]),
)

st.plotly_chart(fig_individual_hours_bar, use_container_width=True)
#-----------------------------------------------------------------------------------
col111, col222 = st.columns(2)

# ----------------------------------------------------------------------------
with col111:

    # ✅ List of staff assignment columns
    staff_columns = ["orig_staff1", "orig_staff2", "orig_staff3"]

    # ✅ Unpivot staff columns to have a single "Staff" column
    staff_matter_data = filtered_matters_ytd.melt(
        id_vars=["MatterCreationDate"], 
        value_vars=staff_columns,  # ✅ Uses correct column names
        var_name="Orig_Staff_Role", 
        value_name="Staff"
    )

    # ✅ Remove empty staff assignments & filter only predefined staff list
    staff_matter_data = staff_matter_data.dropna()
    staff_matter_data = staff_matter_data[staff_matter_data["Staff"].isin(custom_staff_list)]

    # ✅ Count new matters per staff
    new_matters_per_staff = staff_matter_data.groupby("Staff", as_index=False).size()

    # ✅ Create Bar Chart
    fig_ytd_matters = px.bar(
        new_matters_per_staff,
        x="Staff",
        y="size",
        title="YTD New Matters (Per Staff)",
        labels={"size": "New Matters", "Staff": "Staff Member"},
        color="Staff",
        color_discrete_sequence=px.colors.qualitative.Set1
    )

    fig_ytd_matters.update_layout(
        xaxis_title="Staff Member",
        yaxis_title="New Matters",
    )

    st.plotly_chart(fig_ytd_matters, use_container_width=True)
with col222:


    # ✅ Unpivot staff columns to have a single "Staff" column
    weekly_staff_matter_data = filtered_matters_ytd.melt(
        id_vars=["Week"], 
        value_vars=staff_columns,  # ✅ Uses correct column names
        var_name="Orig_Staff_Role", 
        value_name="Staff"
    )

    # ✅ Remove empty staff assignments & filter only predefined staff list
    weekly_staff_matter_data = weekly_staff_matter_data.dropna()
    weekly_staff_matter_data = weekly_staff_matter_data[weekly_staff_matter_data["Staff"].isin(custom_staff_list)]

    # ✅ Count new matters per staff per week
    weekly_new_matters_per_staff = weekly_staff_matter_data.groupby(["Week", "Staff"], as_index=False).size()

    # ✅ Create Bar Chart
    fig_weekly_new_matters = px.bar(
        weekly_new_matters_per_staff,
        x="Week",
        y="size",
        color="Staff",
        title="Weekly New Matters (Per Staff)",
        labels={"size": "New Matters", "Week": "Week Start", "Staff": "Staff Member"},
        color_discrete_sequence=px.colors.qualitative.Set1,
        barmode="group"
    )

    fig_weekly_new_matters.update_layout(
        xaxis_title="Week",
        yaxis_title="New Matters",
        xaxis=dict(tickformat="%Y-%m-%d"),  # ✅ Format weeks properly
    )

    st.plotly_chart(fig_weekly_new_matters, use_container_width=True)