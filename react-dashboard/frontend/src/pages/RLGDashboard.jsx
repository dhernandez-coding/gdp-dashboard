import { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, LabelList, Cell } from 'recharts';
import Plot from 'react-plotly.js';
import KPICard from '../components/KPICard';
import './RLGDashboard.css';

const RLGDashboard = ({ data, dateRange, showGoals, settings }) => {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (data) {
            setLoading(false);
        }
    }, [data]);

    const processedData = useMemo(() => {
        if (!data || !data.revenue || !data.billable_hours || !settings || !settings.custom_staff_list) {
            return null;
        }

        const { revenue, billable_hours, matters, prebills } = data;
        const startDate = new Date(dateRange.start);
        const endDate = new Date(dateRange.end);
        const staffList = settings.custom_staff_list;

        const filteredRevenue = revenue.filter(r => {
            const date = new Date(r.RevShareDate);
            return date >= startDate && date <= endDate && staffList.includes(r.Staff);
        });

        const filteredHours = billable_hours.filter(h => {
            const date = new Date(h.BillableHoursDate);
            const staff = h.StaffAbbreviation || h.Staff;
            return date >= startDate && date <= endDate && staffList.includes(staff);
        });

        // Thresholds
        const thresholdRevenue = settings.treshold_revenue || 2000000;
        const thresholdRevenueStaff = thresholdRevenue / (staffList.length || 1);
        const thresholdHoursWeekly = settings.treshold_hours || 910;
        const thresholdHoursMonthly = thresholdHoursWeekly * 4;

        // KPI Metrics
        const totalRevenue = Math.round(filteredRevenue.reduce((sum, r) => sum + (r.TotalRevShareMonth || 0) + (r.OriginationFees || 0), 0));

        const hoursByMonth = {};
        billable_hours.forEach(h => {
            const date = new Date(h.BillableHoursDate);
            const staff = h.StaffAbbreviation || h.Staff;
            if (staffList.includes(staff)) {
                const month = date.toISOString().slice(0, 7);
                hoursByMonth[month] = (hoursByMonth[month] || 0) + (parseFloat(h.BillableHoursAmount) || 0);
            }
        });

        // KPI Metrics - Use endDate to determine current month
        const currentMonthKey = endDate.toISOString().slice(0, 7);
        const prevMonthDate = new Date(endDate);
        prevMonthDate.setMonth(prevMonthDate.getMonth() - 1);
        const priorMonthKey = prevMonthDate.toISOString().slice(0, 7);

        const currentMonthHours = Math.round(hoursByMonth[currentMonthKey] || 0);
        const priorMonthHours = Math.round(hoursByMonth[priorMonthKey] || 0);

        // 1. Individual YTD Revenue
        const revenuePerStaff = {};
        staffList.forEach(s => revenuePerStaff[s] = 0);
        filteredRevenue.forEach(r => {
            revenuePerStaff[r.Staff] += (r.TotalRevShareMonth || 0) + (r.OriginationFees || 0);
        });
        const revenuePerStaffData = staffList.map(staff => ({
            staff,
            revenue: revenuePerStaff[staff],
            goal: thresholdRevenueStaff
        }));

        // 2. YTD Revenue Trend
        const revByMonth = {};
        filteredRevenue.forEach(r => {
            const month = new Date(r.RevShareDate).toISOString().slice(0, 7);
            revByMonth[month] = (revByMonth[month] || 0) + (r.TotalRevShareMonth || 0) + (r.OriginationFees || 0);
        });

        let cumulative = 0;
        const sortedMonths = Object.keys(revByMonth).sort();
        const ytdRevenueData = sortedMonths.map(month => {
            const monthlyRev = revByMonth[month];
            cumulative += monthlyRev;
            const monthNum = parseInt(month.split('-')[1]);
            return {
                month: new Date(month + '-02').toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                cumulative,
                monthly: monthlyRev,
                goal: (monthNum / 12) * thresholdRevenue
            };
        });

        // 3. Weekly Individual Hours (Week-by-Staff Logic from RLGDashboard.py)
        const weeklyIndividualHoursByStaff = {};

        // Get all Mondays for the last 3 weeks relative to endDate
        const recentWeeks = [];
        const currentEnd = new Date(endDate);
        // Adjust to Monday
        currentEnd.setDate(currentEnd.getDate() - ((currentEnd.getDay() + 6) % 7));

        for (let i = 2; i >= 0; i--) {
            const d = new Date(currentEnd);
            d.setDate(d.getDate() - (i * 7));
            recentWeeks.push(d.toISOString().slice(0, 10));
        }

        filteredHours.forEach(h => {
            const date = new Date(h.BillableHoursDate);
            const monday = new Date(date);
            monday.setDate(date.getDate() - ((date.getDay() + 6) % 7));
            const weekStr = monday.toISOString().slice(0, 10);

            if (recentWeeks.includes(weekStr)) {
                if (!weeklyIndividualHoursByStaff[weekStr]) weeklyIndividualHoursByStaff[weekStr] = {};
                const staff = h.StaffAbbreviation || h.Staff;
                weeklyIndividualHoursByStaff[weekStr][staff] = (weeklyIndividualHoursByStaff[weekStr][staff] || 0) + (parseFloat(h.BillableHoursAmount) || 0);
            }
        });

        const weeklyIndividualDataFlattened = [];
        recentWeeks.forEach(week => {
            staffList.forEach(staff => {
                const hours = weeklyIndividualHoursByStaff[week]?.[staff] || 0;
                const capacity = settings.staff_weekly_goals?.[staff] || 20;
                const avgDaily = hours / 5;

                weeklyIndividualDataFlattened.push({
                    week,
                    staff,
                    groupLabel: `${week} - ${staff}`,
                    hours,
                    capacity,
                    avgDailyText: hours > 0 ? `${avgDaily.toFixed(1)} h/d` : `0.0 h/d`
                });
            });
        });
        const weeklyIndividualData = weeklyIndividualDataFlattened;

        // 4. Weekly Team Hours
        const weeklyTeamHours = {};
        filteredHours.forEach(h => {
            const date = new Date(h.BillableHoursDate);
            const monday = new Date(date);
            monday.setDate(date.getDate() - ((date.getDay() + 6) % 7));
            const weekStr = monday.toISOString().slice(0, 10);
            weeklyTeamHours[weekStr] = (weeklyTeamHours[weekStr] || 0) + (parseFloat(h.BillableHoursAmount) || 0);
        });

        // Get all weeks from the last month in the date range
        const lastMonth = new Date(endDate.getFullYear(), endDate.getMonth(), 1);
        const allWeeksHours = Object.keys(weeklyTeamHours).sort();
        const lastMonthWeeksHours = allWeeksHours.filter(week => {
            const weekDate = new Date(week);
            return weekDate >= lastMonth && weekDate <= endDate;
        });

        const weeklyTeamHoursData = lastMonthWeeksHours.map(week => ({
            week: new Date(week).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            hours: weeklyTeamHours[week] || 0,
            goal: thresholdHoursWeekly
        }));

        // 5. Monthly Team Hours
        const monthlyTeamHoursData = Object.entries(hoursByMonth)
            .sort(([a], [b]) => a.localeCompare(b))
            .filter(([month]) => {
                const date = new Date(month + '-01');
                return date >= startDate && date <= endDate;
            })
            .map(([month, hours]) => ({
                month: new Date(month + '-02').toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                hours,
                goal: thresholdHoursMonthly
            }));

        // 6. YTD New Matters
        const staffMatterCounts = {};
        staffList.forEach(s => staffMatterCounts[s] = 0);
        const staffCols = ['orig_staff1', 'orig_staff2', 'orig_staff3'];

        matters.forEach(m => {
            const date = new Date(m.MatterCreationDate);
            if (date.getFullYear() === endDate.getFullYear() && date <= endDate) {
                staffCols.forEach(col => {
                    const staff = m[col];
                    if (staff && staffList.includes(staff)) {
                        staffMatterCounts[staff]++;
                    }
                });
            }
        });
        const ytdMattersData = staffList.map(staff => ({
            staff,
            count: staffMatterCounts[staff]
        }));

        // 7. Weekly New Matters (YTD only) - Show all weeks from last month
        const weeklyMatters = {};
        matters.forEach(m => {
            const date = new Date(m.MatterCreationDate);
            // Only include matters from the current year (YTD filter like Streamlit)
            if (date.getFullYear() === endDate.getFullYear() && date <= endDate) {
                const monday = new Date(date);
                monday.setDate(date.getDate() - ((date.getDay() + 6) % 7));
                const weekStr = monday.toISOString().slice(0, 10);

                if (!weeklyMatters[weekStr]) weeklyMatters[weekStr] = {};
                staffCols.forEach(col => {
                    const staff = m[col];
                    if (staff && staffList.includes(staff)) {
                        weeklyMatters[weekStr][staff] = (weeklyMatters[weekStr][staff] || 0) + 1;
                    }
                });
            }
        });

        // Get all weeks from the last month in the date range
        const lastMonthMatters = new Date(endDate.getFullYear(), endDate.getMonth(), 1);
        const allWeeks = Object.keys(weeklyMatters).sort();
        const lastMonthWeeks = allWeeks.filter(week => {
            const weekDate = new Date(week);
            return weekDate >= lastMonthMatters && weekDate <= endDate;
        });

        const weeklyMattersData = lastMonthWeeks.map(week => ({
            week: new Date(week).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            ...weeklyMatters[week]
        }));


        return {
            metrics: { totalRevenue, currentMonthHours, priorMonthHours },
            revenuePerStaffData,
            ytdRevenueData,
            weeklyIndividualData,
            weeklyTeamHoursData,
            monthlyTeamHoursData,
            ytdMattersData,
            weeklyMattersData,
            prebills: prebills || {}
        };
    }, [data, dateRange, settings]);

    if (loading || !processedData) return <div className="loading-container"><div className="spinner"></div></div>;

    const { metrics, revenuePerStaffData, ytdRevenueData, weeklyIndividualData, weeklyTeamHoursData, monthlyTeamHoursData, ytdMattersData, weeklyMattersData, prebills } = processedData;
    const colors = ['#4facfe', '#00f2fe', '#64ffda', '#f093fb', '#f5576c', '#48c6ef', '#6a85b6', '#a8edea', '#fed6e3'];
    const monthsShort = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    return (
        <div className="dashboard-page">
            <div className="kpi-grid">
                <KPICard title="Total Revenue" value={`$${metrics.totalRevenue.toLocaleString()}`} icon="💰" />
                <KPICard title="Current Month Hours" value={`${metrics.currentMonthHours.toLocaleString()}`} subtitle="hours" icon="⏱️" />
                <KPICard title="Prior Month Hours" value={`${metrics.priorMonthHours.toLocaleString()}`} subtitle="hours" icon="📊" />
            </div>

            <div className="charts-section">
                <h2 className="section-title">Performance Overview</h2>
                <div className="charts-grid">
                    <div className="chart-card glass-card">
                        <h3 className="chart-title">Individual YTD Revenue</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={revenuePerStaffData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="staff" />
                                <YAxis tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} />
                                <Tooltip
                                    formatter={(val) => [`Revenue: $${Math.round(val).toLocaleString()}`]}
                                    contentStyle={{ backgroundColor: '#222', border: 'none' }}
                                    itemStyle={{ color: '#fff' }}
                                    labelStyle={{ display: 'none' }}
                                />
                                <Bar dataKey="revenue" fill="#4facfe" radius={[4, 4, 0, 0]} />
                                {showGoals && <ReferenceLine y={revenuePerStaffData[0]?.goal} stroke="#ff4d4d" strokeDasharray="3 3" label={{ position: 'right', value: 'Goal', fill: '#ff4d4d', fontSize: 10 }} />}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="chart-card glass-card">
                        <h3 className="chart-title">YTD Revenue Trend</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={ytdRevenueData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis tickFormatter={(val) => `$${(val / 1000000).toFixed(1)}M`} />
                                <Tooltip
                                    formatter={(val) => [`Revenue: $${Math.round(val).toLocaleString()}`]}
                                    contentStyle={{ backgroundColor: '#222', border: 'none' }}
                                    itemStyle={{ color: '#fff' }}
                                    labelStyle={{ display: 'none' }}
                                />
                                <Bar dataKey="cumulative" fill="#00f2fe" radius={[4, 4, 0, 0]} />
                                {showGoals && <Line type="monotone" dataKey="goal" stroke="#ff4d4d" strokeDasharray="5 5" dot={false} strokeWidth={2} />}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="section-divider"></div>

                <h2 className="section-title">Weekly Individual Hours</h2>
                <div className="chart-card full-width glass-card">
                    <Plot
                        data={[
                            {
                                x: weeklyIndividualData.map(d => d.groupLabel),
                                y: weeklyIndividualData.map(d => d.capacity),
                                type: 'bar',
                                name: 'Capacity',
                                marker: {
                                    color: 'rgba(136, 146, 176, 0.3)',
                                    line: {
                                        color: 'rgba(136, 146, 176, 0.5)',
                                        width: 1
                                    }
                                },
                                hoverinfo: 'skip'
                            },
                            {
                                x: weeklyIndividualData.map(d => d.groupLabel),
                                y: weeklyIndividualData.map(d => d.hours),
                                type: 'bar',
                                name: 'Hours Worked',
                                marker: {
                                    color: '#64ffda'
                                },
                                text: weeklyIndividualData.map(d => d.avgDailyText),
                                textposition: 'outside',
                                textfont: {
                                    size: 10,
                                    color: '#8892b0'
                                },
                                hovertemplate: '<b>%{x}</b><br>Hours Count: %{y:.1f}<br>Avg: %{text}<extra></extra>'
                            }
                        ]}
                        layout={{
                            barmode: 'overlay',
                            bargap: 0.4,
                            xaxis: {
                                title: '',
                                tickangle: -45,
                                tickfont: { size: 10, color: '#8892b0' },
                                showgrid: false,
                                showline: false
                            },
                            yaxis: {
                                title: 'Total Hours Worked',
                                tickfont: { size: 12, color: '#8892b0' },
                                gridcolor: 'rgba(255,255,255,0.1)',
                                showline: false
                            },
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: '#8892b0' },
                            legend: {
                                orientation: 'h',
                                yanchor: 'top',
                                y: -0.2,
                                xanchor: 'center',
                                x: 0.5
                            },
                            margin: { b: 120, t: 20, l: 60, r: 20 },
                            height: 500,
                            hovermode: 'closest'
                        }}
                        config={{ responsive: true, displayModeBar: true, displaylogo: false }}
                        style={{ width: '100%', height: '500px' }}
                    />
                </div>

                <div className="section-divider"></div>

                <div className="charts-grid">
                    <div className="chart-card glass-card">
                        <h3 className="chart-title">Weekly Team Hours</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={weeklyTeamHoursData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="week" />
                                <YAxis />
                                <Tooltip
                                    formatter={(value) => [`Hours: ${value.toFixed(1)}`]}
                                    contentStyle={{ backgroundColor: '#222', border: 'none' }}
                                    itemStyle={{ color: '#fff' }}
                                    labelStyle={{ display: 'none' }}
                                />
                                <Bar dataKey="hours" fill="#4facfe" radius={[4, 4, 0, 0]} />
                                {showGoals && <ReferenceLine y={weeklyTeamHoursData[0]?.goal} stroke="#ff4d4d" strokeDasharray="3 3" label={{ position: 'top', value: 'Goal', fill: '#ff4d4d', fontSize: 10 }} />}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="chart-card glass-card">
                        <h3 className="chart-title">Monthly Team Hours</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={monthlyTeamHoursData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis />
                                <Tooltip
                                    formatter={(value) => [`Hours: ${value.toFixed(1)}`]}
                                    contentStyle={{ backgroundColor: '#222', border: 'none' }}
                                    itemStyle={{ color: '#fff' }}
                                    labelStyle={{ display: 'none' }}
                                />
                                <Bar dataKey="hours" fill="#00f2fe" radius={[4, 4, 0, 0]} />
                                {showGoals && <ReferenceLine y={monthlyTeamHoursData[0]?.goal} stroke="#ff4d4d" strokeDasharray="3 3" label={{ position: 'top', value: 'Goal', fill: '#ff4d4d', fontSize: 10 }} />}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="section-divider"></div>

                <div className="charts-grid">
                    <div className="chart-card glass-card">
                        <h3 className="chart-title">YTD New Matters</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={ytdMattersData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="staff" />
                                <YAxis />

                                <Tooltip
                                    formatter={(value, name, props) => {
                                        const staffName = props.payload.staff;
                                        return [`${staffName}: ${value} matters`];
                                    }}
                                    contentStyle={{ backgroundColor: '#222', border: 'none' }}
                                    itemStyle={{ color: '#fff' }}
                                    labelStyle={{ display: 'none' }}
                                />

                                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                    {ytdMattersData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="chart-card glass-card">
                        <h3 className="chart-title">Weekly New Matters</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={weeklyMattersData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="week" />
                                <YAxis />

                                <Tooltip
                                    formatter={(value, name) => [`${name}: ${value} matters`]}
                                    contentStyle={{ backgroundColor: '#222', border: 'none' }}
                                    itemStyle={{ color: '#fff' }}
                                    labelStyle={{ display: 'none' }}
                                />

                                <Legend />

                                {settings.custom_staff_list.map((staff, i) => (
                                    <Bar key={staff} dataKey={staff} fill={colors[i % colors.length]} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="section-divider"></div>

                <h2 className="section-title">Prebills Status</h2>
                <div className="prebills-matrix-container glass-card">
                    <table className="prebills-matrix">
                        <thead>
                            <tr>
                                <th>Name</th>
                                {monthsShort.map(m => <th key={m}>{m}</th>)}
                            </tr>
                        </thead>
                        <tbody>
                            {Object.entries(prebills).map(([staff, monthsData]) => (
                                <tr key={staff}>
                                    <td className="staff-name">{staff}</td>
                                    {monthsShort.map(month => (
                                        <td key={month}>
                                            <div className={`status-dot ${monthsData[month] === 'Yes' ? 'status-yes' : 'status-no'}`}></div>
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default RLGDashboard;
