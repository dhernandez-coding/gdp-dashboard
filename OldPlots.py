#---- Old Plots-----#

import streamlit as st
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