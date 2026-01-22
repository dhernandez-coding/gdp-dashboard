import { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
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
        if (!data || !data.revenue || !data.billable_hours || !settings) return null;

        const { revenue, billable_hours, matters } = data;
        const startDate = new Date(dateRange.start);
        const endDate = new Date(dateRange.end);

        const filteredRevenue = revenue.filter(r => {
            const date = new Date(r.RevShareDate);
            return date >= startDate && date <= endDate;
        });

        const filteredHours = billable_hours.filter(h => {
            const date = new Date(h.BillableHoursDate);
            return date >= startDate && date <= endDate;
        });

        // KPIs
        const totalRevenue = filteredRevenue.reduce((sum, r) => sum + (r.TotalRevShareMonth || 0) + (r.OriginationFees || 0), 0);

        const hoursByMonth = {};
        filteredHours.forEach(h => {
            const month = new Date(h.BillableHoursDate).toISOString().slice(0, 7);
            hoursByMonth[month] = (hoursByMonth[month] || 0) + (h.BillableHoursAmount || 0);
        });

        const months = Object.keys(hoursByMonth).sort();
        const currentMonth = months[months.length - 1];
        const priorMonth = months[months.length - 2];

        const currentMonthHours = hoursByMonth[currentMonth] || 0;
        const priorMonthHours = hoursByMonth[priorMonth] || 0;

        // Charts data
        const revenueByStaff = {};
        filteredRevenue.forEach(r => {
            const staff = r.Staff;
            if (staff && settings.custom_staff_list.includes(staff)) {
                revenueByStaff[staff] = (revenueByStaff[staff] || 0) + (r.TotalRevShareMonth || 0) + (r.OriginationFees || 0);
            }
        });
        const revenueByStaffData = Object.entries(revenueByStaff).map(([staff, revenue]) => ({ staff, revenue }));

        const revenueByMonth = {};
        filteredRevenue.forEach(r => {
            const month = new Date(r.RevShareDate).toISOString().slice(0, 7);
            revenueByMonth[month] = (revenueByMonth[month] || 0) + (r.TotalRevShareMonth || 0) + (r.OriginationFees || 0);
        });

        let cumulative = 0;
        const ytdRevenueData = Object.entries(revenueByMonth)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([month, revenue]) => {
                cumulative += revenue;
                return {
                    month: new Date(month + '-01').toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                    revenue,
                    cumulative
                };
            });

        const monthlyHoursData = Object.entries(hoursByMonth)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([month, hours]) => ({
                month: new Date(month + '-01').toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                hours
            }));

        // Weekly individual hours
        const weeklyIndividualHours = {};
        const last6Weeks = [];
        const today = new Date();
        for (let i = 5; i >= 0; i--) {
            const d = new Date(today);
            d.setDate(d.getDate() - d.getDay() + 1 - (i * 7));
            last6Weeks.push(d.toISOString().slice(0, 10));
        }

        filteredHours.forEach(h => {
            const date = new Date(h.BillableHoursDate);
            const monday = new Date(date.setDate(date.getDate() - date.getDay() + 1)).toISOString().slice(0, 10);
            if (last6Weeks.includes(monday)) {
                if (!weeklyIndividualHours[monday]) weeklyIndividualHours[monday] = {};
                const staff = h.StaffAbbreviation;
                weeklyIndividualHours[monday][staff] = (weeklyIndividualHours[monday][staff] || 0) + (h.BillableHoursAmount || 0);
            }
        });

        const weeklyIndividualData = last6Weeks.map(week => {
            const entry = { week };
            settings.custom_staff_list.forEach(staff => {
                entry[staff] = weeklyIndividualHours[week]?.[staff] || 0;
            });
            return entry;
        });

        // Matters
        const ytdMatters = {};
        const weeklyMatters = {};
        const staffCols = ['orig_staff1', 'orig_staff2', 'orig_staff3'];
        matters.forEach(m => {
            const date = new Date(m.MatterCreationDate);
            if (date >= startDate && date <= endDate) {
                staffCols.forEach(col => {
                    const staff = m[col];
                    if (staff && settings.custom_staff_list.includes(staff)) {
                        ytdMatters[staff] = (ytdMatters[staff] || 0) + 1;
                        const monday = new Date(new Date(date).setDate(date.getDate() - date.getDay() + 1)).toISOString().slice(0, 10);
                        if (!weeklyMatters[monday]) weeklyMatters[monday] = {};
                        weeklyMatters[monday][staff] = (weeklyMatters[monday][staff] || 0) + 1;
                    }
                });
            }
        });

        const ytdMattersData = Object.entries(ytdMatters).map(([staff, count]) => ({ staff, count }));
        const weeklyMattersData = Object.entries(weeklyMatters)
            .sort(([a], [b]) => a.localeCompare(b))
            .slice(-4)
            .map(([week, counts]) => ({
                week: new Date(week).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                ...counts
            }));

        return {
            totalRevenue, currentMonthHours, priorMonthHours,
            revenueByStaffData, ytdRevenueData, monthlyHoursData,
            weeklyIndividualData, ytdMattersData, weeklyMattersData
        };
    }, [data, dateRange, settings]);

    if (loading || !processedData) return <div className="loading-container"><div className="spinner"></div></div>;

    const {
        totalRevenue, currentMonthHours, priorMonthHours,
        revenueByStaffData, ytdRevenueData, monthlyHoursData,
        weeklyIndividualData, ytdMattersData, weeklyMattersData
    } = processedData;

    const colors = ['#052B48', '#3371A1', '#4CA7ED', '#76C7E0', '#0288A7', '#E3C26D', '#E3B36D', '#DAA520', '#F0E68C'];

    return (
        <div className="dashboard-page">
            <div className="kpi-grid">
                <KPICard title="Total Revenue" value={`$${totalRevenue.toLocaleString()}`} icon="💰" />
                <KPICard title="Current Month Hours" value={`${currentMonthHours.toLocaleString()}`} subtitle="hours" icon="⏱️" />
                <KPICard title="Prior Month Hours" value={`${priorMonthHours.toLocaleString()}`} subtitle="hours" icon="📊" />
            </div>

            <div className="charts-section">
                <h2 className="section-title">Revenue & Goals</h2>
                <div className="charts-grid">
                    <div className="chart-card">
                        <h3 className="chart-title">Individual YTD Revenue</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={revenueByStaffData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="staff" />
                                <YAxis tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} />
                                <Tooltip formatter={(val) => `$${val.toLocaleString()}`} />
                                <Bar dataKey="revenue" fill="#399db7" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="chart-card">
                        <h3 className="chart-title">YTD Revenue Trend</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={ytdRevenueData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} />
                                <Tooltip formatter={(val) => `$${val.toLocaleString()}`} />
                                <Bar dataKey="cumulative" fill="#399db7" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <h2 className="section-title">Weekly Performance</h2>
                <div className="chart-card">
                    <h3 className="chart-title">Weekly Individual Hours (Last 6 Weeks)</h3>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={weeklyIndividualData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="week" tickFormatter={(val) => new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            {settings.custom_staff_list.map((staff, i) => (
                                <Bar key={staff} dataKey={staff} fill={colors[i % colors.length]} name={staff} />
                            ))}
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <h2 className="section-title">New Matters</h2>
                <div className="charts-grid">
                    <div className="chart-card">
                        <h3 className="chart-title">YTD New Matters</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={ytdMattersData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="staff" />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="count" fill="#4CA7ED" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="chart-card">
                        <h3 className="chart-title">Recent Weekly Matters</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={weeklyMattersData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="week" />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                {settings.custom_staff_list.map((staff, i) => (
                                    <Bar key={staff} dataKey={staff} fill={colors[i % colors.length]} stackId="a" />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RLGDashboard;
