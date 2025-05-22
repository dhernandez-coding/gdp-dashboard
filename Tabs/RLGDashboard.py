import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import datetime
import numpy as np
import json


# ✅ Set default date range (One year ago to today)
PREBILLS_FILE = Path(__file__).parents[1] / "data" / "prebills.json"

today = pd.Timestamp.today()
default_start_date = today - pd.DateOffset(years=1)
default_end_date = pd.to_datetime(today).to_period("M").end_time ##- pd.DateOffset(days=2)

# ✅ Define Colors
PRIMARY_COLOR = "#399db7"  # Light blue
DARK_BLUE = "#052b48"      # Dark blue
COMPLEMENTARY_COLOR1 = "#FF6F61"  # Coral (for differentiation)
COMPLEMENTARY_COLOR2 = "#F4A261"  # Warm orange (for better contrast)
custom_palette = [
    "#052B48",  # deep navy
    "#3371A1",  # steel blue
    "#4CA7ED",  # sky blue
    "#76C7E0",  # soft sky (lighter)
    "#0288A7",  # teal‑blue (darker/livelier)

    "#E3C26D",  # mustard
    "#E3B36D",  # warm tan
    "#DAA520",  # goldenrod (richer gold)
    "#F0E68C",  # khaki yellow (softer)
]

def load_data():
    """Load datasets from the /data folder and preprocess dates."""
    data_path = Path(__file__).parents[1] / "data"

    # Load CSVs
    revenue = pd.read_csv(data_path / "RevShareNewLogic.csv", parse_dates=["RevShareDate"])
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", parse_dates=["BillableHoursDate"])
    matters = pd.read_csv(data_path / "vMatters.csv", parse_dates=["MatterCreationDate"])
    

    # ✅ Apply Date Transformations Once (for efficiency)
    billable_hours["Month"] = billable_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    billable_hours["Week"] = billable_hours["BillableHoursDate"] - pd.to_timedelta(billable_hours["BillableHoursDate"].dt.dayofweek, unit="D")

    revenue["MonthDate"] = revenue["RevShareDate"].dt.to_period("M").dt.to_timestamp()
    revenue["WeekDate"] = revenue["RevShareDate"] - pd.to_timedelta(revenue["RevShareDate"].dt.dayofweek, unit="D")

    matters["Week"] = matters["MatterCreationDate"] - pd.to_timedelta(matters["MatterCreationDate"].dt.dayofweek, unit="D")

    return revenue, billable_hours, matters


# Load data
revenue, billable_hours, matters = load_data()

def run_rlg_dashboard(start_date, end_date, show_goals):

    treshold_hours = st.session_state["treshold_hours"]
    treshold_revenue = st.session_state["treshold_revenue"]

    custom_staff_list = st.session_state["custom_staff_list"]
    treshold_revenue_staff = treshold_revenue / float(len(custom_staff_list))
    treshold_hours_staff_monthly = treshold_hours / 12
    treshold_hours_staff_weekly = treshold_hours_staff_monthly / 4

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
    #filtered_revenue = filtered_revenue.rename(columns={"StaffAbbreviation": "Staff"})
    
    # ✅ Filter Data to Include Only Predefined Staff
    filtered_team_hours = filtered_team_hours[filtered_team_hours["Staff"].isin(custom_staff_list)]
    filtered_revenue = filtered_revenue[filtered_revenue["Staff"].isin(custom_staff_list)]
    
    # ----------------------------------------------------------------------------
    ## Transformating data 
    # ✅ Convert Dates for Monthly Aggregation
    filtered_revenue["MonthDate"] = filtered_revenue["RevShareDate"].dt.to_period("M").dt.to_timestamp()


    filtered_team_hours["Month"] = filtered_team_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    
    # ✅ Convert Dates for Weekly Aggregation
    filtered_revenue["WeekDate"] = filtered_revenue["RevShareDate"] - pd.to_timedelta(filtered_revenue["RevShareDate"].dt.dayofweek, unit="D")
    filtered_team_hours["Week"] = filtered_team_hours["BillableHoursDate"] - pd.to_timedelta(filtered_team_hours["BillableHoursDate"].dt.dayofweek, unit="D")
    filtered_revenue["Total"]=filtered_revenue["TotalRevShareMonth"] + filtered_revenue["OriginationFees"]
    # ✅ Identify the Last Selected Month from Date Slider
    last_selected_month = max(filtered_revenue["MonthDate"])  # Last selected month

    # ✅ 1️⃣ Revenue Per Staff (Monthly)
    revenue_per_staff_monthly = (
        filtered_revenue.groupby(["MonthDate", "Staff"], as_index=False)["Total"].sum()
    )
    # # ✅ Multiply by 0.8 to account for 20% commission
    # revenue_per_staff_monthly.loc[:, "TimeEntryBilledAmount"] *= 1 #0.8
    
    # ✅ 2️⃣ Total Team Revenue (Monthly)
    total_team_revenue_monthly = revenue_per_staff_monthly.groupby("MonthDate", as_index=False)["Total"].sum()
    # Multiply for the 0.8 to account for 20% commission
    total_team_revenue_monthly.loc[:, "Total"] *= 1 #
    
    # ✅ 3️⃣ Billable Hours Per Staff (Weekly)
    billable_hours_per_staff_weekly = filtered_team_hours.groupby(["Week", "Staff"], as_index=False)["BillableHoursAmount"].sum()
    
    # ✅ 4️⃣ Billable Hours Per Staff (Monthly)
    billable_hours_per_staff_monthly = filtered_team_hours.groupby(["Month", "Staff"], as_index=False)["BillableHoursAmount"].sum()
    
    # ✅ 5️⃣ Total Team Billable Hours (Weekly)
    total_team_hours_weekly = billable_hours_per_staff_weekly.groupby("Week", as_index=False)["BillableHoursAmount"].sum()
    
    # ✅ 6️⃣ Total Team Billable Hours (Monthly)
    total_team_hours_monthly = billable_hours_per_staff_monthly.groupby("Month", as_index=False)["BillableHoursAmount"].sum()
    
    # ✅ Sort by Month to ensure proper cumulative sum
    total_team_revenue_monthly = total_team_revenue_monthly.sort_values(by="MonthDate")
    
    # ✅ Compute the cumulative sum
    total_team_revenue_monthly["CumulativeRevenue"] = total_team_revenue_monthly["Total"].cumsum()
    
    # ✅ Convert MatterCreationDate to Weekly Period
    filtered_matters_ytd["Week"] = filtered_matters_ytd["MatterCreationDate"] - pd.to_timedelta(filtered_matters_ytd["MatterCreationDate"].dt.dayofweek, unit="D")
    
    # ✅ Get current and prior month based on the latest selected month
    current_month = str(pd.to_datetime(last_selected_month).to_period("M"))
    prior_month = str((pd.to_datetime(last_selected_month) - pd.DateOffset(months=1)).to_period("M"))
    
    
    #------------------------------------------YTD CALCULATIONS-------------------------------------------- 
    # ✅ Step 1: Get the selected year from `end_date`
    selected_year = end_date.year
    
    # ✅ Step 2: Generate all 12 months in the selected year (Jan → Dec)
    all_months = pd.date_range(start=pd.Timestamp(selected_year, 1, 1), 
                               end=pd.Timestamp(selected_year, 12, 31), 
                               freq="MS")
    
    # ✅ Step 3: Create a DataFrame with all 12 months
    all_months_df = pd.DataFrame({"MonthDate": all_months, "Year": selected_year})
    
    ytd_revenue = total_team_revenue_monthly[
    total_team_revenue_monthly["MonthDate"].dt.year == selected_year
]
    # ✅ Step 4: Filter `total_team_revenue_monthly` for the selected year only
    ytd_revenue = total_team_revenue_monthly[
        total_team_revenue_monthly["MonthDate"].dt.year == selected_year

    ]
    
    # ✅ Step 5: Merge with the full 12-month dataset to ensure no months are missing
    ytd_revenue = all_months_df.merge(ytd_revenue, on=["MonthDate"], how="left")
    
    # ✅ Step 6: Fill missing revenue values with 0
    ytd_revenue["Total"] = ytd_revenue["Total"].fillna(0)
    
    # ✅ Step 7: Compute cumulative revenue (YTD)
    ytd_revenue["CumulativeRevenue"] = ytd_revenue["Total"].cumsum()
    
    # ✅ Step 8: Identify the last month where revenue is greater than 0
    last_revenue_month = ytd_revenue[ytd_revenue["Total"] > 0]["MonthDate"].max()
    
    # ✅ Step 9: Set cumulative revenue to 0 for months after the last revenue month
    ytd_revenue.loc[ytd_revenue["MonthDate"] > last_revenue_month, "CumulativeRevenue"] = 0
    
    # ✅ Step 10: Ensure sorting by Month
    ytd_revenue["MonthDate"] = pd.to_datetime(ytd_revenue["MonthDate"])  # Convert to datetime for proper sorting
    ytd_revenue = ytd_revenue.sort_values("MonthDate")
    
    # ✅ Step 11: Format month labels for better display
    ytd_revenue["MonthLabel"] = ytd_revenue["MonthDate"].dt.strftime("%b %Y")  # Example: "Jan 2025"
    
    # ✅ Step 12: Create a goal line based on the goal set up on the settings for the year
    ytd_revenue["GoalRevenue"] = np.linspace(0, treshold_revenue, num=12) 
    
    #----Month Filtering --------------------------------------------------
    current_month_hours = total_team_hours_monthly.loc[
        total_team_hours_monthly["Month"] == current_month, "BillableHoursAmount"
    ].sum()
    
    prior_month_hours = total_team_hours_monthly.loc[
        total_team_hours_monthly["Month"] == prior_month, "BillableHoursAmount"
    ].sum()
    # ---------------------------------------------------------------------------- 
        
    # ✅ KPI METRICS (Dynamically Updating)
    total_revenue = filtered_revenue["Total"].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_revenue:,.0f}")
    col2.metric("Current Month Hours", f"{current_month_hours:,.0f} hours")
    col3.metric("Prior Month Hours", f"{prior_month_hours:,.0f} hours")

    st.markdown("---")

    # ----------------------------------------------------------------------------
    # ✅ WEEKLY TEAM HOURS & YTD REVENUE CHARTS
    st.subheader("Weekly Team Hours & YTD Revenue", divider="gray")
    col1, col2 = st.columns(2)
    # Filter only prior months
    total_team_hours_monthly["MonthDate"] = pd.to_datetime(total_team_hours_monthly["Month"])
    prior_months_team_hours = total_team_hours_monthly[total_team_hours_monthly["MonthDate"] < last_selected_month]
    # ✅ Convert BillableHoursDate to Weekly Period & Aggregate
    # 🎯 PLOT 1: Cumulative Revenue (Bar Chart)
    with col1:
    
        # ✅ REVENUE PER STAFF (Bar Chart)
        fig1 = px.bar(
            filtered_revenue,
            x="Staff",
            y="Total",
            color="Staff",
            title=f"{selected_year} Individual YTD Revenue",
            labels={"Total": "Revenue ($)"},
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


    # 🎯 PLOT 2: CumulativeRevenue (Bar Chart)
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
                name="Goal Revenue",
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
    filtered_team_hours["Week"] = filtered_team_hours["BillableHoursDate"] - pd.to_timedelta(
        filtered_team_hours["BillableHoursDate"].dt.dayofweek, unit="D"
    )

    # ✅ Aggregate by Week and Staff
    weekly_individual_hours = (
        filtered_team_hours.groupby(["Week", "Staff"], as_index=False)["BillableHoursAmount"].sum()
    )
    # ✅ Filter: Only the 6 most recent weeks before or equal to selected end_date
    valid_weeks = weekly_individual_hours["Week"].unique()
    recent_weeks = sorted([w for w in valid_weeks if w <= end_date])[-6:]
    weekly_individual_hours = weekly_individual_hours[weekly_individual_hours["Week"].isin(recent_weeks)]

    # ✅ Compute Weekly Average Daily Hours (Total Weekly Hours / 5)
    weekly_individual_hours["AvgDailyHours"] = weekly_individual_hours["BillableHoursAmount"] / 5
    weekly_individual_hours["AvgDailyText"] = weekly_individual_hours["AvgDailyHours"].apply(lambda x: f"{x:.1f} h/d")
    weekly_individual_hours["AvgWorked"] = weekly_individual_hours["AvgDailyHours"] * 5
    weekly_individual_hours["WeeklyGoal"] = treshold_hours_staff_weekly

    # ✅ Create composite label per bar: Week + Staff
    weekly_individual_hours["GroupLabel"] = weekly_individual_hours["Week"].dt.strftime("%Y-%m-%d") + " - " + weekly_individual_hours["Staff"]

   # Define a color palette and map each staff to a distinct color
    staff_list = weekly_individual_hours["Staff"].unique()
    palette = custom_palette  # you can choose any Plotly qualitative palette
    color_map = {staff: palette[i % len(palette)] for i, staff in enumerate(staff_list)}
    
    # Apply the mapping to create a list of colors corresponding to each row
    weekly_individual_hours["StaffColor"] = weekly_individual_hours["Staff"].map(color_map)
    
    # Build the overlaid figure
    fig = go.Figure()
    
    # Bar 1: Goal (light gray)
    fig.add_trace(go.Bar(
        x=weekly_individual_hours["GroupLabel"],
        y=weekly_individual_hours["WeeklyGoal"],
        name="Goal (19h)",
        showlegend=False,
        marker_color="rgba(128,128,128,0.3)",
        offsetgroup="bars",
        hoverinfo="skip"
    ))
    
    # Bar 2: Avg (semi-transparent)
    fig.add_trace(go.Bar(
        x=weekly_individual_hours["GroupLabel"],
        y=weekly_individual_hours["AvgWorked"],
        showlegend=False,
        name="Avg Daily × 5",
        marker_color="rgba(100,149,237,0.4)",
        offsetgroup="bars"
    ))
    
    # Bar 3: Actual (distinct color per staff)
    for staff in staff_list:
        df = weekly_individual_hours[weekly_individual_hours["Staff"] == staff]
        fig.add_trace(go.Bar(
            x=df["GroupLabel"],
            y=df["BillableHoursAmount"],
            name=staff,                                  # staff name shows up in legend
            marker_color=color_map[staff],
            text=df["AvgDailyText"],
            textposition="outside"
        ))
    
    fig.update_layout(
        title="Weekly Individual Hours (Goal vs Avg vs Actual)",
        xaxis_title="Staff per Week",
        yaxis_title="Total Hours Worked",
        barmode="overlay",
        bargap=0.4,
        xaxis_tickangle=-45,
    
        # ← place legend horizontally below the plot
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-.45,        # move it below the x-axis
            xanchor="center",
            x=0.5
        ),
        margin=dict(
        b=0,       # increase from b=100 up to whatever you need
        t=0,        # top margin (optional)
        l=0,        # left margin (optional)
        r=0         # right margin (optional)
        )  # give extra bottom margin for the legend
    )
    
    st.plotly_chart(fig, use_container_width=True)

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
    
        # 🎯 Step 9: PLOT Team Hours

        months = pd.period_range(
            start=start_date.to_period("M"),
            end=end_date.to_period("M"),
            freq="M"
        ).astype(str).tolist()    # e.g. ['2025-01','2025-02',...,'2025-05']
        
        # 2) Filter & aggregate as before
        prior_months_team_hours = total_team_hours_monthly[
            total_team_hours_monthly["Month"].isin(months)
        ].copy()
        
        # 3) Turn Month into an ordered Categorical
        prior_months_team_hours["Month"] = pd.Categorical(
            prior_months_team_hours["Month"],
            categories=months,
            ordered=True
        )
        
        # 4) Now plot, and Plotly will automatically include every category
        fig_prior_team_hours = px.bar(
            prior_months_team_hours,
            x="Month",
            y="BillableHoursAmount",
            title="Team Hours - Prior Months",
            labels={"Month":"Month", "BillableHoursAmount":"Hours Worked"},
            color_discrete_sequence=[DARK_BLUE],
            category_orders={"Month": months}   # also enforce in the legend/order
        )
        
        # 5) Final layout: no need for explicit tickvals now
        fig_prior_team_hours.update_layout(
            xaxis_title="Month",
            yaxis_title="Hours Worked",
            bargap=0.2
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

    # ✅ Matrix for Prebills
    # Define 12 months based on today
    # ✅ Custom CSS to align selectboxes and labels
    st.markdown("""
    <style>
        .stSelectbox {
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
        }
        .element-container:has(.stSelectbox) {
            display: flex;
            align-items: center;
        }
        .row-label {
            display: flex;
            align-items: center;
            height: 100%;
            font-weight: 500;
            padding-left: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    months = pd.date_range(start=pd.Timestamp.today().replace(month=1, day=1), periods=12, freq="MS").strftime("%b").tolist()
    # ✅ Load existing data or initialize
    prebills_data = {}
    if PREBILLS_FILE.exists():
        try:
            with open(PREBILLS_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    prebills_data = json.loads(content)
        except json.JSONDecodeError:
            st.warning("⚠️ The prebills file is corrupted or empty. Initializing fresh data.")

    # ✅ Ensure all staff and months exist in the data
    for staff in custom_staff_list:
        if staff not in prebills_data:
            prebills_data[staff] = {}
        for month in months:
            if month not in prebills_data[staff]:
                prebills_data[staff][month] = "No"

    # ✅ Build editable matrix
    st.title("Prebills Back On Time")
    st.write("Update Yes/No per staff and month:")

    with st.form("prebills_form"):
        updated_data = {}

        # Header
        cols = st.columns(len(months) + 1)
        cols[0].markdown("**Name**")
        for i, month in enumerate(months):
            cols[i + 1].markdown(f"**{month}**")

        # Rows
        for staff in custom_staff_list:
            row = st.columns(len(months) + 1)
            row[0].markdown(f"<div class='row-label'>{staff}</div>", unsafe_allow_html=True)
            updated_data[staff] = {}
            for i, month in enumerate(months):
                key = f"{staff}_{month}"
                updated_data[staff][month] = row[i + 1].selectbox(
                    "Prebills Response", 
                    options=["Yes", "No"],
                    index=["Yes", "No"].index(prebills_data[staff][month]),
                    key=key,
                    label_visibility="collapsed"
                )

        # Save button
        if st.form_submit_button("Save"):
            with open(PREBILLS_FILE, "w") as f:
                json.dump(updated_data, f, indent=4)
            st.success("✅ Matrix saved successfully!")

