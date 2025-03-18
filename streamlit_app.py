import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ✅ Define Colors
PRIMARY_COLOR = "#399db7"  # Light blue
DARK_BLUE = "#052b48"      # Dark blue
COMPLEMENTARY_COLOR1 = "#FF6F61"  # Coral (for differentiation)
COMPLEMENTARY_COLOR2 = "#F4A261"  # Warm orange (for better contrast)
logo_path = Path(__file__).parent / "data" / "resolution.png"
# ✅ Set Streamlit Page Config
st.set_page_config(
    page_title="Time Entry Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load Data Function
@st.cache_data
def load_data():
    """Load datasets from the /data folder."""
    data_path = Path(__file__).parent / "data"

    staff_revenue = pd.read_csv(data_path / "staff_revenue.csv")
    team_hours = pd.read_csv(data_path / "team_hours.csv")
    individual_hours = pd.read_csv(data_path / "individual_hours.csv")

    # Convert Date Columns
    individual_hours["WeekStartDate"] = pd.to_datetime(individual_hours["WeekStartDate"])

    return staff_revenue, team_hours, individual_hours

# Load data
staff_revenue, team_hours, individual_hours = load_data()

# ----------------------------------------------------------------------------
# HEADER WITH COMPANY LOGO
header_bg_color = "#052b48"  # Dark blue background for header
logo_path = Path(__file__).parent / "data" / "resolution.png"

st.markdown(
    f"""
    <div style="background-color:{header_bg_color}; padding:20px; text-align:center; border-radius:5px;">
        <h1 style="color:white; margin-bottom:5px;">Time Entry Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Now Display the Logo Properly
if logo_path.exists():
    st.image(str(logo_path), width=200)
else:
    st.warning("Logo not found! Please check that 'resolution.png' is inside the 'data' folder.")

st.markdown("---")

# ----------------------------------------------------------------------------
# ✅ KPI METRICS (Simplified)
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${staff_revenue['YTD_Actual'].sum():,.0f}")
col2.metric("Total Team Hours", f"{team_hours['Total_Hours'].sum():,.0f} hours")
col3.metric("Avg Weekly Hours", f"{individual_hours.groupby('WeekStartDate')['Total_Hours'].mean().mean():,.1f} hours")

st.markdown("---")

# ----------------------------------------------------------------------------
# ✅ STAFF REVENUE (BAR CHART WITH DISTINCT COLORS)
st.subheader("YTD Revenue per Staff", divider="gray")

st.markdown(
    """
    <style>
        /* Change background and text color of selected options */
        span[data-baseweb="tag"] {
            background-color: #052b48 !important;  /* Dark Blue */
            color: white !important;
            border-radius: 8px;
            padding: 5px 10px;
        }

        /* Change hover effect for selected items */
        span[data-baseweb="tag"]:hover {
            background-color: #399db7 !important; /* Light Blue */
            color: white !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

selected_staff = st.multiselect(
    "Filter by Staff:",
    staff_revenue["Staff"].unique(),
    default=staff_revenue["Staff"].unique()
)

filtered_revenue = staff_revenue[staff_revenue["Staff"].isin(selected_staff)]


fig1 = px.bar(
    filtered_revenue,
    x="Staff",
    y="YTD_Actual",
    color="Staff",
    title="YTD Revenue per Staff",
    labels={"YTD_Actual": "Revenue ($)"},
    color_discrete_sequence=[PRIMARY_COLOR]
)

fig1.add_hline(
    y=300000,  # Y-Axis Position for the threshold
    line_dash="dash",  # Makes it a dashed line
    line_color=COMPLEMENTARY_COLOR1,  # Coral color for visibility
    annotation_text="Target: $300K",  # Label for the line
    annotation_position="top left",
    annotation_font_size=12,
    annotation_font_color=COMPLEMENTARY_COLOR1
)

fig1.update_layout(
    xaxis_title="", 
    yaxis_title="Revenue ($)", 
    showlegend=False
)

st.plotly_chart(fig1, use_container_width=True)

# ----------------------------------------------------------------------------
# ✅ MONTHLY TEAM HOURS (BAR CHART WITH THRESHOLD LINE)
st.subheader("Team Hours per Month", divider="gray")

# ✅ Month Mapping (Numbers → Strings)
MONTHS_MAP = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

# ✅ Reverse Mapping for Filtering (Strings → Numbers)
REVERSE_MONTHS_MAP = {v: k for k, v in MONTHS_MAP.items()}

# ✅ Get Min & Max Month Numbers from Data
min_month = int(team_hours["Month"].min())
max_month = int(team_hours["Month"].max())

# ✅ Convert Month Numbers to Labels for Display
month_labels = [MONTHS_MAP[i] for i in range(min_month, max_month + 1)]

# ✅ Custom Slider Using Month Names
selected_months = st.select_slider(
    "Select a month range:",
    options=month_labels,  # Display month names instead of numbers
    value=(month_labels[0], month_labels[-1])  # Default range: first to last month
)

# ✅ Convert Selected Month Names Back to Numbers for Filtering
selected_min_month = REVERSE_MONTHS_MAP[selected_months[0]]
selected_max_month = REVERSE_MONTHS_MAP[selected_months[1]]

# ✅ Filter Data Based on Selected Months
filtered_team_hours = team_hours[
    (team_hours["Month"] >= selected_min_month) & (team_hours["Month"] <= selected_max_month)
].copy()

# ✅ Map Month Numbers to Names for Proper Labels
filtered_team_hours["Month_Name"] = filtered_team_hours["Month"].map(MONTHS_MAP)

# ✅ Create Plotly Bar Chart
fig2 = px.bar(
    filtered_team_hours,
    x="Month_Name",  # Now using month names instead of numbers
    y="Total_Hours",
    title="Total Team Hours by Month",
    labels={"Total_Hours": "Hours Worked", "Month_Name": "Month"},
    color_discrete_sequence=["#052b48"]  # Dark Blue Bars
)

# ✅ Add Threshold Line at 910 Hours
fig2.add_hline(
    y=910,
    line_dash="dash",
    line_color="red",
    annotation_text="Threshold: 910 Hours",
    annotation_position="top left"
)

fig2.update_layout(
    xaxis_title="Month", 
    yaxis_title="Total Hours"
)

# ✅ Display in Streamlit
st.plotly_chart(fig2, use_container_width=True)

# ----------------------------------------------------------------------------

# ✅ WEEKLY INDIVIDUAL HOURS (LINE CHART)
st.subheader("Individual Hours by Week", divider="gray")

selected_staff_weekly = st.multiselect("Select Staff:", individual_hours["Staff"].unique(), default=individual_hours["Staff"].unique()[:5])

filtered_individual_hours = individual_hours[individual_hours["Staff"].isin(selected_staff_weekly)]

fig3 = px.line(
    filtered_individual_hours,
    x="WeekStartDate",
    y="Total_Hours",
    color="Staff",
    markers=True,
    title="Weekly Individual Hours",
    labels={"WeekStartDate": "Week", "Total_Hours": "Hours Worked"}
)
fig3.update_layout(
    xaxis_title="Week", 
    yaxis_title="Total Hours"
)

st.plotly_chart(fig3, use_container_width=True)

# individual_hours_2024 = individual_hours[individual_hours["WeekStartDate"].dt.year == 2024]
# staff_revenue_2024 = staff_revenue[staff_revenue["Year"] == 2024]

# ✅ Weekly Aggregation for Team Hours (2024)
weekly_hours_agg = individual_hours.groupby("WeekStartDate", as_index=False)["Total_Hours"].sum()

# ✅ Monthly Aggregation for YTD Revenue (Cumulative)
staff_revenue["Month"] = pd.to_datetime(staff_revenue["Month"], format="%m")  # Ensure Month is datetime
monthly_revenue_agg = staff_revenue.groupby("Month", as_index=False)["YTD_Actual"].sum()
monthly_revenue_agg["YTD_Cumulative"] = monthly_revenue_agg["YTD_Actual"].cumsum()  # Compute cumulative revenue

# ✅ Side-by-Side Layout for New Charts
st.subheader("2024 Weekly Team Hours & YTD Revenue", divider="gray")
col1, col2 = st.columns(2)

# 🎯 PLOT 1: 2024 Weekly Team Hours (Bar Chart)
with col1:
    fig_weekly_hours = px.bar(
        weekly_hours_agg,
        x="WeekStartDate",
        y="Total_Hours",
        title="2024 Weekly Team Hours",
        labels={"WeekStartDate": "Week", "Total_Hours": "Hours Worked"},
        color_discrete_sequence=[DARK_BLUE]
    )
    fig_weekly_hours.update_layout(xaxis_title="Week", yaxis_title="Hours Worked")
    st.plotly_chart(fig_weekly_hours, use_container_width=True)

# 🎯 PLOT 2: 2024 YTD Revenue (Cumulative Line Chart)
with col2:
    fig_ytd_revenue = px.line(
        monthly_revenue_agg,
        x="Month",
        y="YTD_Cumulative",
        markers=True,
        title="2024 YTD Revenue (Cumulative)",
        labels={"YTD_Cumulative": "Cumulative Revenue ($)", "Month": "Month"},
        color_discrete_sequence=[COMPLEMENTARY_COLOR1]
    )
    fig_ytd_revenue.update_layout(xaxis_title="Month", yaxis_title="Cumulative Revenue ($)")
    st.plotly_chart(fig_ytd_revenue, use_container_width=True)


# ----------------------------------------------------------------------------
# ✅ EXPANDABLE RAW DATA TABLES (TITLES IN DARK BLUE)
st.subheader("Data Tables", divider="gray")

with st.expander("View Staff Revenue Data"):
    st.dataframe(staff_revenue.style.format({"YTD_Actual": "${:,.0f}"}))

with st.expander("View Team Hours Data"):
    st.dataframe(team_hours.style.format({"Total_Hours": "{:,.0f}"}))

with st.expander("View Individual Hours Data"):
    st.dataframe(individual_hours.style.format({"Total_Hours": "{:,.0f}"}))
st.subheader("Data Tables", divider="gray")
# st.markdown("---")
# st.markdown(f"<h6 style='text-align: center; color: {DARK_BLUE};'>Built with ❤️ in Streamlit</h6>", unsafe_allow_html=True)
