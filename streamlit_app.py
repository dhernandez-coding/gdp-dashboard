import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import datetime
import numpy as np
import json

# ✅ Set default date range (One year ago to today)
SETTINGS_FILE = Path(__file__).parent / "data" / "settings.json"
def load_threshold_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"treshold_hours": 910, "treshold_revenue": 2000000}

def save_threshold_settings(thresholds: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(thresholds, f, indent=4)

if "treshold_hours" not in st.session_state or "treshold_revenue" not in st.session_state:
    saved_settings = load_threshold_settings()
    st.session_state["treshold_hours"] = saved_settings["treshold_hours"]
    st.session_state["treshold_revenue"] = saved_settings["treshold_revenue"]

today = pd.Timestamp.today()
default_start_date = today - pd.DateOffset(years=1)
default_end_date = today - pd.DateOffset(days=2)
treshold_hours = st.session_state["treshold_hours"]
treshold_revenue = st.session_state["treshold_revenue"]

custom_staff_list = ["AEZ", "BPL", "CAJ", "JER", "JRJ", "RAW", "WMJ"]
treshold_revenue_staff = treshold_revenue / float(len(custom_staff_list))
treshold_hours_staff_monthly = treshold_hours / 12
treshold_hours_staff_weekly = treshold_hours_staff_monthly / 4
# ✅ Define Colors
PRIMARY_COLOR = "#399db7"  # Light blue
DARK_BLUE = "#052b48"      # Dark blue
COMPLEMENTARY_COLOR1 = "#FF6F61"  # Coral (for differentiation)
COMPLEMENTARY_COLOR2 = "#F4A261"  # Warm orange (for better contrast)
custom_palette = ["#052B48", "#4CA7ED", "#3371A1", "#265578", "#19384F"]

# ✅ Define logo path
logo_path = Path(__file__).parent / "data" / "resolution.png"

# ✅ Set Streamlit Page Config (Favicon only works with a string path)
st.set_page_config(
    page_title="Time Entry Dashboard",
    page_icon=str(logo_path) if logo_path.exists() else "📊",
    layout="wide"
)


# ✅ Load Data Function
@st.cache_data(ttl=86400)  # Cache expires after 86400 seconds (24 hours)

def load_data():
    """Load datasets from the /data folder and preprocess dates."""
    data_path = Path(__file__).parent / "data"

    # Load CSVs
    revenue = pd.read_csv(data_path / "vTimeEntries.csv", parse_dates=["TimeEntryDate"])
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", parse_dates=["BillableHoursDate"])
    matters = pd.read_csv(data_path / "vMatters.csv", parse_dates=["MatterCreationDate"])

    # ✅ Apply Date Transformations Once (for efficiency)
    billable_hours["Month"] = billable_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    billable_hours["Week"] = billable_hours["BillableHoursDate"] - pd.to_timedelta(billable_hours["BillableHoursDate"].dt.dayofweek, unit="D")

    revenue["Month"] = revenue["TimeEntryDate"].dt.to_period("M").astype(str)
    revenue["Week"] = revenue["TimeEntryDate"] - pd.to_timedelta(revenue["TimeEntryDate"].dt.dayofweek, unit="D")

    matters["Week"] = matters["MatterCreationDate"] - pd.to_timedelta(matters["MatterCreationDate"].dt.dayofweek, unit="D")

    return revenue, billable_hours, matters

# Load data
revenue, billable_hours, matters = load_data()

# ✅ Predefined Staff List (Always Show These)


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
page = st.sidebar.radio("Select Page", ["Dashboard", "Settings"])
min_date = min(revenue["TimeEntryDate"].min(), billable_hours["BillableHoursDate"].min(), matters["MatterCreationDate"].min())
start_of_year = pd.Timestamp(today.year, 1, 1)
if min_date < pd.Timestamp("2020-01-01"):
    min_date = pd.Timestamp("2020-01-01")
max_date = max(revenue["TimeEntryDate"].max(), billable_hours["BillableHoursDate"].max(), matters["MatterCreationDate"].max())

# Make sure default_start_date and default_end_date are within bounds
default_start_date = max(start_of_year, min_date)
default_end_date = min(today, max_date)

date_range = st.sidebar.date_input(
    "Select Date Range",
    [default_start_date, default_end_date],
    min_value=min_date,
    max_value=max_date
)
show_goals = st.sidebar.checkbox("Show Goal Lines", value=True)
# Convert to Timestamp for filtering
start_date = pd.Timestamp(date_range[0])
end_date = pd.Timestamp(date_range[1])

# Apply date filter to all datasets
filtered_revenue = revenue[(revenue["TimeEntryDate"] >= start_date) & (revenue["TimeEntryDate"] <= end_date)]
filtered_team_hours = billable_hours[(billable_hours["BillableHoursDate"] >= start_date) & (billable_hours["BillableHoursDate"] <= end_date)]
filtered_matters = matters[(matters["MatterCreationDate"] >= start_date) & (matters["MatterCreationDate"] <= end_date)]
# ✅ Filter matters created within the selected year-to-date range
filtered_matters_ytd = filtered_matters[
    (filtered_matters["MatterCreationDate"] >= pd.Timestamp(start_date.year, 1, 1)) &
    (filtered_matters["MatterCreationDate"] <= end_date)
]

# ✅ Ensure Correct Column Naming (Rename StaffAbbreviation to Staff)
filtered_team_hours = filtered_team_hours.rename(columns={"StaffAbbreviation": "Staff"})
#filtered_revenue = filtered_revenue.rename(columns={"StaffAbbreviation": "Staff"})

# ✅ Filter Data to Include Only Predefined Staff
filtered_team_hours = filtered_team_hours[filtered_team_hours["Staff"].isin(custom_staff_list)]
filtered_revenue = filtered_revenue[filtered_revenue["Staff"].isin(custom_staff_list)]

st.markdown("---")
# ----------------------------------------------------------------------------
## Transformating data 
# ✅ Convert Dates for Monthly Aggregation
filtered_revenue["Month"] = filtered_revenue["TimeEntryDate"].dt.to_period("M").astype(str)
filtered_team_hours["Month"] = filtered_team_hours["BillableHoursDate"].dt.to_period("M").astype(str)

# ✅ Convert Dates for Weekly Aggregation
filtered_revenue["Week"] = filtered_revenue["TimeEntryDate"] - pd.to_timedelta(filtered_revenue["TimeEntryDate"].dt.dayofweek, unit="D")
filtered_team_hours["Week"] = filtered_team_hours["BillableHoursDate"] - pd.to_timedelta(filtered_team_hours["BillableHoursDate"].dt.dayofweek, unit="D")

# ✅ Identify the Last Selected Month from Date Slider
last_selected_month = max(filtered_revenue["Month"])  # Last selected month

# ✅ 1️⃣ Revenue Per Staff (Monthly)
revenue_per_staff_monthly = (
    filtered_revenue.groupby(["Month", "Staff"], as_index=False)["TimeEntryBilledAmount"].sum()
)
# ✅ Multiply by 0.8 to account for 20% commission
revenue_per_staff_monthly.loc[:, "TimeEntryBilledAmount"] *= 1 #0.8

# ✅ 2️⃣ Total Team Revenue (Monthly)
total_team_revenue_monthly = revenue_per_staff_monthly.groupby("Month", as_index=False)["TimeEntryBilledAmount"].sum()
# Multiply for the 0.8 to account for 20% commission
total_team_revenue_monthly.loc[:, "TimeEntryBilledAmount"] *= 1 #

# ✅ 3️⃣ Billable Hours Per Staff (Weekly)
billable_hours_per_staff_weekly = filtered_team_hours.groupby(["Week", "Staff"], as_index=False)["BillableHoursAmount"].sum()

# ✅ 4️⃣ Billable Hours Per Staff (Monthly)
billable_hours_per_staff_monthly = filtered_team_hours.groupby(["Month", "Staff"], as_index=False)["BillableHoursAmount"].sum()

# ✅ 5️⃣ Total Team Billable Hours (Weekly)
total_team_hours_weekly = billable_hours_per_staff_weekly.groupby("Week", as_index=False)["BillableHoursAmount"].sum()

# ✅ 6️⃣ Total Team Billable Hours (Monthly)
total_team_hours_monthly = billable_hours_per_staff_monthly.groupby("Month", as_index=False)["BillableHoursAmount"].sum()

# ✅ Sort by Month to ensure proper cumulative sum
total_team_revenue_monthly = total_team_revenue_monthly.sort_values(by="Month")

# ✅ Compute the cumulative sum
total_team_revenue_monthly["CumulativeRevenue"] = total_team_revenue_monthly["TimeEntryBilledAmount"].cumsum()

# ✅ Convert MatterCreationDate to Weekly Period
filtered_matters_ytd["Week"] = filtered_matters_ytd["MatterCreationDate"] - pd.to_timedelta(filtered_matters_ytd["MatterCreationDate"].dt.dayofweek, unit="D")
#------------------------------------------YTD CALCULATIONS-------------------------------------------- 
# ✅ Step 1: Get the selected year from `end_date`
selected_year = end_date.year

# ✅ Step 2: Generate all 12 months in the selected year (Jan → Dec)
all_months = pd.date_range(start=pd.Timestamp(selected_year, 1, 1), 
                           end=pd.Timestamp(selected_year, 12, 31), 
                           freq="MS").strftime("%Y-%m").tolist()

# ✅ Step 3: Create a DataFrame with all 12 months
all_months_df = pd.DataFrame({"Month": all_months, "Year": selected_year})

# ✅ Step 4: Filter `total_team_revenue_monthly` for the selected year only
ytd_revenue = total_team_revenue_monthly[
    total_team_revenue_monthly["Month"].str.startswith(str(selected_year))
]

# ✅ Step 5: Merge with the full 12-month dataset to ensure no months are missing
ytd_revenue = all_months_df.merge(ytd_revenue, on=["Month"], how="left")

# ✅ Step 6: Fill missing revenue values with 0
ytd_revenue["TimeEntryBilledAmount"] = ytd_revenue["TimeEntryBilledAmount"].fillna(0)

# ✅ Step 7: Compute cumulative revenue (YTD)
ytd_revenue["CumulativeRevenue"] = ytd_revenue["TimeEntryBilledAmount"].cumsum()

# ✅ Step 8: Identify the last month where revenue is greater than 0
last_revenue_month = ytd_revenue[ytd_revenue["TimeEntryBilledAmount"] > 0]["Month"].max()

# ✅ Step 9: Set cumulative revenue to 0 for months after the last revenue month
ytd_revenue.loc[ytd_revenue["Month"] > last_revenue_month, "CumulativeRevenue"] = 0

# ✅ Step 10: Ensure sorting by Month
ytd_revenue["Month"] = pd.to_datetime(ytd_revenue["Month"])  # Convert to datetime for proper sorting
ytd_revenue = ytd_revenue.sort_values("Month")

# ✅ Step 11: Format month labels for better display
ytd_revenue["MonthLabel"] = ytd_revenue["Month"].dt.strftime("%b %Y")  # Example: "Jan 2025"

# ✅ Step 12: Create a goal line for $2M revenue over the year
ytd_revenue["GoalRevenue"] = np.linspace(0, 2000000, num=12) 


# ----------------------------------------------------------------------------
if page == "Dashboard":

    
    # ✅ KPI METRICS (Dynamically Updating)
    total_revenue = filtered_revenue["TimeEntryBilledAmount"].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
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
            y="TimeEntryBilledAmount",
            color="Staff",
            title=f"{selected_year} Individual YTD Revenue",
            labels={"TimeEntryBilledAmount": "Revenue ($)"},
            color_discrete_sequence=[PRIMARY_COLOR],
            hover_data=[]
        )
        # ✅ Add a horizontal line for the threshold revenue per staff
        if show_goals:
            fig1.add_hline(
                y=treshold_revenue_staff,
                line_dash="dash",
                line_color="red",
            )

            fig1.add_annotation(
                x=filtered_revenue["Staff"].max(),  # rightmost staff member on x-axis
                y=treshold_revenue_staff,
                text=f"Threshold: ${treshold_revenue_staff:,.0f}",
                showarrow=False,
                font=dict(color="red", size=12),
                align="left",
                bgcolor="white",
                bordercolor="red",
                borderwidth=1,
                borderpad=4,
                xanchor="left",
                yanchor="bottom"
            ) 
        fig1.update_layout(xaxis_title="", yaxis_title="Revenue ($)", showlegend=False)
        fig1.update_traces(hoverinfo="skip", hovertemplate=None)
        st.plotly_chart(fig1, use_container_width=True)


    # 🎯 PLOT 2: prior_team_hours (Bar Chart)
    with col2:

        fig_ytd_revenue = px.bar(
            ytd_revenue,
            x="MonthLabel",  # ✅ Use formatted month labels
            y="CumulativeRevenue",
            title=f"YTD Revenue ({selected_year})",
            labels={"CumulativeRevenue": "Cumulative Revenue ($)", "MonthLabel": "Month"},
            color_discrete_sequence=[PRIMARY_COLOR] # ✅ Generate a sample goal revenue
        )   
        if show_goals:
            fig_ytd_revenue.add_scatter(
                x=ytd_revenue["MonthLabel"], 
                y=ytd_revenue["GoalRevenue"],
                mode="lines",
                name="Goal Revenue ($2M)",
                line=dict(color="red", dash="dash")  # Green dashed line for clarity
            )
        # ✅ Step 11: Ensure the X-axis shows **exactly 12 months**
        fig_ytd_revenue.update_layout(
            xaxis_title="Month",
            yaxis_title="Cumulative Revenue ($)",
            xaxis=dict(
                tickmode="array",
                tickvals=ytd_revenue["MonthLabel"],  # ✅ Ensures all 12 months are displayed
                ticktext=ytd_revenue["MonthLabel"]  # ✅ Show "Jan 2025", "Feb 2025", ..., "Dec 2025"
            )
        )
        st.plotly_chart(fig_ytd_revenue, use_container_width=True)



    # ----------------------------------------------------------------------------
    # ✅ WEEKLY INDIVIDUAL HOURS (Grouped Bar Chart)
    st.subheader("Weekly Individual Hours", divider="gray")

    # ✅ Convert BillableHoursDate to Weekly Period & Aggregate
    filtered_team_hours["Week"] = filtered_team_hours["BillableHoursDate"] - pd.to_timedelta(filtered_team_hours["BillableHoursDate"].dt.dayofweek, unit="D")

    # ✅ Aggregate by Week and Staff
    weekly_individual_hours = filtered_team_hours.groupby(["Week", "Staff"], as_index=False)["BillableHoursAmount"].sum()

    # ✅ Compute Weekly Average Daily Hours (Total Weekly Hours / 5)
    weekly_individual_hours["AvgDailyHours"] = weekly_individual_hours["BillableHoursAmount"] / 5

    # ✅ Create text column formatted as string (e.g. "7.4 h/d")
    weekly_individual_hours["AvgDailyText"] = weekly_individual_hours["AvgDailyHours"].apply(lambda x: f"{x:.1f} h/d")


    # ✅ Create Grouped Bar Chart with Enhanced Tooltip
    fig_individual_hours_bar = px.bar(
        weekly_individual_hours,
        x="Week",
        y="BillableHoursAmount",
        color="Staff",
        title="Weekly Individual Hours Worked",
        labels={"BillableHoursAmount": "Total Hours Worked", "Week": "Week Start", "Staff": "Staff Member"},
        color_discrete_sequence=custom_palette,
        barmode="group",
        text="AvgDailyText" # ✅ Display average daily hours text
        #hover_data={"AvgDailyHours": ":.2f"}  # ✅ Show Avg Daily Hours in Tooltip (formatted to 2 decimals)
    )
    # ✅ Position the labels on top of the bars
    fig_individual_hours_bar.update_traces(textposition="outside")
    if show_goals:
        fig_individual_hours_bar.add_hline(
                y=treshold_hours_staff_weekly,
                line_dash="dash",
                line_color="red",
        )

        fig_individual_hours_bar.add_annotation(
            x=weekly_individual_hours["Week"].max(),  # latest week (rightmost x-axis value)
            y=treshold_hours_staff_weekly,
            text=f"Individual minimum: {treshold_hours_staff_weekly:,.0f}",
            showarrow=False,
            font=dict(color="red", size=12),
            align="left",
            bgcolor="white",
            bordercolor="red",
            borderwidth=1,
            borderpad=4,
            xanchor="left",
            yanchor="bottom"
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

        if show_goals:
            team_weekly_goal = treshold_hours_staff_weekly * len(custom_staff_list)
            fig_weekly_hours.add_hline(
                y=team_weekly_goal,
                line_dash="dash",
                line_color="red"
            )
            fig_weekly_hours.add_annotation(
                x=total_team_hours_weekly["Week"].max(),
                y=team_weekly_goal,
                text=f"Team Weekly Goal: {team_weekly_goal:,.0f} hrs",
                showarrow=False,
                font=dict(color="red", size=12),
                align="left",
                bgcolor="white",
                bordercolor="red",
                borderwidth=1,
                borderpad=4,
                xanchor="left",
                yanchor="bottom"
            )
        fig_weekly_hours.update_layout(
            xaxis_title="Week",
            yaxis_title="Hours Worked",
            xaxis=dict(tickformat="%Y-%m-%d")  # Format dates for better readability
        )

        st.plotly_chart(fig_weekly_hours, use_container_width=True)

    with col22:

        # 🎯 Step 9: PLOT Team Hours

        fig_prior_team_hours = px.bar(
            prior_months_team_hours,  # ✅ Filtered dataset
            x="Month",
            y="BillableHoursAmount",
            title="Team Hours - Prior Months",
            labels={"Month": "Month", "BillableHoursAmount": "Hours Worked"},
            color_discrete_sequence=[DARK_BLUE]
        )
        if show_goals:
            fig_prior_team_hours.add_hline(
                y=treshold_hours,
                line_dash="dash",
                line_color="red",
            )
            fig_prior_team_hours.add_annotation(
                x=prior_months_team_hours["Month"].max(),
                y=treshold_hours,
                text=f"Team Monthly Goal: {treshold_hours:,.0f} hrs",
                showarrow=False,
                font=dict(color="red", size=12),
                align="left",
                bgcolor="white",
                bordercolor="red",
                borderwidth=1,
                borderpad=4,
                xanchor="left",
                yanchor="bottom"
            )

        fig_prior_team_hours.update_layout(
            xaxis_title="Month",
            yaxis_title="Hours Worked",
            xaxis=dict(tickmode="array", tickvals=prior_months_team_hours["Month"])
        )

        st.plotly_chart(fig_prior_team_hours, use_container_width=True)

    # ✅ MONTHLY INDIVIDUAL HOURS (Grouped Bar Chart)
    st.subheader("Monthly Individual Hours", divider="gray")

    # ✅ Ensure the Month column is datetime for sorting
    filtered_team_hours["Month"] = filtered_team_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    monthly_individual_hours = filtered_team_hours.groupby(["Month", "Staff"], as_index=False)["BillableHoursAmount"].sum()

    # ✅ Sort Month and create readable label
    monthly_individual_hours["MonthDate"] = pd.to_datetime(monthly_individual_hours["Month"])
    monthly_individual_hours = monthly_individual_hours.sort_values(by=["Staff", "MonthDate"])
    monthly_individual_hours["MonthLabel"] = monthly_individual_hours["MonthDate"].dt.strftime("%b")  # Jan, Feb...

    # ✅ Create grouped bar chart: x = Staff, color = Month, grouped by staff
    fig_individual_hours_bar = px.bar(
        monthly_individual_hours,
        x="Staff",
        y="BillableHoursAmount",
        color="MonthLabel",
        barmode="group",
        title="Monthly Individual Hours Worked",
        labels={
            "BillableHoursAmount": "Total Hours Worked",
            "Staff": "Staff Member",
            "MonthLabel": "Month"
        },
        color_discrete_sequence=custom_palette
    )

    # ✅ Optional: Add threshold line and annotation
    if show_goals:
        fig_individual_hours_bar.add_hline(
            y=treshold_hours_staff_monthly,
            line_dash="dash",
            line_color="red",
        )

        fig_individual_hours_bar.add_annotation(
            x=monthly_individual_hours["Staff"].iloc[-1],  # last staff in x-axis
            y=treshold_hours_staff_monthly,
            text=f"Individual minimum: {treshold_hours_staff_monthly:,.0f}",
            showarrow=False,
            font=dict(color="red", size=12),
            align="right",
            bgcolor="white",
            bordercolor="red",
            borderwidth=1,
            borderpad=4,
            xanchor="left",
            yanchor="bottom"
        )

    # ✅ Final layout
    fig_individual_hours_bar.update_layout(
        xaxis_title="Staff Member",
        yaxis_title="Total Hours Worked",
        legend_title="Month",
        bargap=0.15
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
            title="YTD New Matters",
            labels={"size": "New Matters", "Staff": "Staff Member"},
            color="Staff",
            color_discrete_sequence=custom_palette
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
            title="Weekly New Matters",
            labels={"size": "New Matters", "Week": "Week Start", "Staff": "Staff Member"},
            color_discrete_sequence=custom_palette,
            barmode="group"
        )

        fig_weekly_new_matters.update_layout(
            xaxis_title="Week",
            yaxis_title="New Matters",
            xaxis=dict(tickformat="%Y-%m-%d"),  # ✅ Format weeks properly
        )

        st.plotly_chart(fig_weekly_new_matters, use_container_width=True)
    # ----------------------------------------------------------------------------
elif page == "Settings":
    st.title("🔧 Dashboard Settings")

    # Let user adjust values
    new_hours = st.number_input(
        "Team Goal: Total Billable Hours (Annual)",
        min_value=0,
        value=st.session_state["treshold_hours"],
        step=10
    )

    new_revenue = st.number_input(
        "Team Goal: Total Revenue ($)",
        min_value=0,
        value=st.session_state["treshold_revenue"],
        step=10000
    )

    # Only update file if values changed
    if (new_hours != st.session_state["treshold_hours"]) or (new_revenue != st.session_state["treshold_revenue"]):
        st.session_state["treshold_hours"] = new_hours
        st.session_state["treshold_revenue"] = new_revenue

        save_threshold_settings({
            "treshold_hours": new_hours,
            "treshold_revenue": new_revenue
        })

        st.success("✅ Thresholds updated and saved!")

    # Show breakdown
    st.markdown("### Calculated Thresholds Per Person")
    st.write(f"**Monthly hours per lawyer**: {new_hours / 12:,.2f} hours")
    st.write(f"**Weekly hours per lawyer**: {new_hours / 12 / 4:,.2f} hours")
    st.write(f"**Revenue per lawyer**: ${new_revenue / len(custom_staff_list):,.2f}")

