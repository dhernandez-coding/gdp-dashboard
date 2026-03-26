import { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getRevShareData } from '../services/api';
import KPICard from '../components/KPICard';
import './RevShare.css';

const RevShare = ({ settings, dateRange }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedStaff, setSelectedStaff] = useState('');
    const [userRole, setUserRole] = useState({ is_admin: false, staff_code: '' });
    const [error, setError] = useState(null);

    const formatMoney = (val) => {
        if (val === null || val === undefined) return '';
        return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const result = await getRevShareData();
                setData(result);

                // Set User Role if returned by API
                if (result.user_role) {
                    setUserRole(result.user_role);
                    // If not admin, force select their own staff code
                    if (!result.user_role.is_admin && result.user_role.staff_code) {
                        setSelectedStaff(result.user_role.staff_code);
                    } else if (settings?.custom_staff_list?.length > 0) {
                        setSelectedStaff(settings.custom_staff_list[0]);
                    }
                } else {
                    // Fallback for previous expected behavior
                    if (settings?.custom_staff_list?.length > 0) {
                        setSelectedStaff(settings.custom_staff_list[0]);
                    }
                }

            } catch (err) {
                setError('Failed to load revenue share data');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [settings]);

    const filteredData = useMemo(() => {
        if (!data || !selectedStaff) return null;

        const startDate = new Date(dateRange.start);
        const endDate = new Date(dateRange.end);

        const filterByDateAndStaff = (list, dateField) => {
            return (list || []).filter(item => {
                const date = new Date(item[dateField]);
                // Staff might be 'Staff' or 'StaffAbbreviation'
                const staff = item.Staff || item.StaffAbbreviation;
                return date >= startDate && date <= endDate && staff === selectedStaff;
            });
        };

        const revShare = filterByDateAndStaff(data.revshare, 'RevShareDate').map(item => ({
            ...item,
            flatFeeHours: (Number(item.FONEHours) || 0) + (Number(item.FMONHours) || 0),
            flatFeeRevenue: (Number(item.FONERevenue) || 0) + (Number(item.FMONRevenue) || 0),
            threshold: 14000,
            eligibleRevenue: Math.max(0, (Number(item.TotalRevShareMonth) || 0) - 14000),
            productionShare: (Number(item.RevTier1) || 0) + (Number(item.RevTier2) || 0) + (Number(item.RevTier3) || 0)
        }));

        const te1 = filterByDateAndStaff(data.te_type1, 'TimeEntryDate');
        const te2 = filterByDateAndStaff(data.te_type2, 'TimeEntryDate');
        const te3 = filterByDateAndStaff(data.te_type3, 'TimeEntryDate');

        const totalProductionRevenue = revShare.reduce((sum, item) => sum + (item.TotalRevShareMonth || 0), 0);
        const totalRevenueShare = revShare.reduce((sum, item) => sum + (item.RevShareTotal || 0), 0);
        const totalHours = [...te1, ...te2, ...te3].reduce((sum, item) => sum + (item.TimeEntryAmount || 0), 0);

        // Payout by MOnth Logic - Stacked (Flat vs Hourly)
        // Using revShare summary data instead of reconstructing from Time Entries
        const chartData = revShare.map(item => {
            const flatRev = (parseFloat(item.FONERevenue) || 0) + (parseFloat(item.FMONRevenue) || 0);
            const hourlyRev = parseFloat(item.HourlyRevenue) || 0;
            return {
                month: new Date(item.RevShareDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                timestamp: new Date(item.RevShareDate).getTime(),
                FlatFee: flatRev,
                Hourly: hourlyRev,
                Total: flatRev + hourlyRev
            };
        }).sort((a, b) => a.timestamp - b.timestamp);

        // Top 10 Matters Logic - Based on HOURS (TimeEntryAmount)
        const clientStats = {};
        const allEntries = [...te1, ...te2, ...te3];

        allEntries.forEach(item => {
            if (!item.TimeEntryName) return;
            // Expected format: "ID - CLIENT NAME - MATTER - DESCRIPTION..."
            const parts = item.TimeEntryName.split(' - ');
            // Combine Client Name and Matter Name (indices 1 and 2)
            let matterName = 'Unknown';
            if (parts.length > 2) {
                matterName = `${parts[1].trim()} - ${parts[2].trim()}`;
            } else if (parts.length > 1) {
                matterName = parts[1].trim();
            }

            if (!clientStats[matterName]) {
                clientStats[matterName] = 0;
            }
            // User requested Total TimeEntryAmount (Hours)
            clientStats[matterName] += (parseFloat(item.TimeEntryAmount) || 0);
        });

        const topClientsData = Object.entries(clientStats)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10);

        return { totalProductionRevenue, totalRevenueShare, totalHours, chartData, topClientsData, revShare, te1, te2, te3 };
    }, [data, selectedStaff, dateRange]);

    if (loading) return <div className="loading-container"><div className="spinner"></div></div>;
    if (error) return <div className="error-message">{error}</div>;

    const staffList = settings?.custom_staff_list || [];

    // Dynamic Columns Helper (Kept for reference, unused by default now)
    const renderTable = (dataList, title) => {
        // ... (existing helper code, omitted for brevity if needed, but keeping for safety)
        if (!dataList || dataList.length === 0) return null;
        const keys = Object.keys(dataList[0]);
        const moneyKeys = ['TimeEntryRate', 'TimeEntryGross', 'TimeEntryBilledAmount', 'TotalPayout', 'Rate', 'Gross', 'Billed', 'Payout'];
        return (
            <section className="table-section glass-card mt-4">
                {/* ... */}
            </section>
        )
    }

    return (
        <div className="revshare-page">
            <div className="page-header">
                <h1 className="page-title">Revenue Share Review - {selectedStaff}</h1>

                {/* Only show selector if Admin */}
                {userRole.is_admin && (
                    <div className="staff-selector-container">
                        <label htmlFor="staff-select">Select Staff:</label>
                        <select
                            id="staff-select"
                            className="input staff-select"
                            value={selectedStaff}
                            onChange={(e) => setSelectedStaff(e.target.value)}
                        >
                            {staffList.map(staff => (
                                <option key={staff} value={staff}>{staff}</option>
                            ))}
                        </select>
                    </div>
                )}
            </div>

            <div className="kpi-grid">
                <KPICard title="Total Production Revenue" value={formatMoney(filteredData?.totalProductionRevenue)} icon="💰" />
                <KPICard title="Total Hours" value={`${(filteredData?.totalHours || 0).toFixed(1)} hours`} icon="⏱️" />
                <KPICard title="Total Revenue Share" value={formatMoney(filteredData?.totalRevenueShare)} icon="💸" />
            </div>

            {/* Rev Share Table - Specific Layout */}
            <section className="table-section glass-card mt-4">
                <h3>Revenue Share Summary</h3>
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Staff</th>
                                <th>Month</th>
                                <th>Flat Fee Hours</th>
                                <th>Avg Collection Rate</th>
                                <th>Flat Fee Revenue</th>
                                <th>Hourly Hours Collected</th>
                                <th>Hourly Revenue</th>
                                <th>Total Prod Revenue</th>
                                <th>Threshold</th>
                                <th>Eligible for Rev Share</th>
                                <th>Tier 1 Share</th>
                                <th>Tier 2 Share</th>
                                <th>Tier 3 Share</th>
                                <th>Prod Rev Share</th>
                                <th>Origination Rev Share</th>
                                <th>Total Rev Share</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredData?.revShare.map((row, i) => (
                                <tr key={i}>
                                    <td>{row.Staff}</td>
                                    <td>{new Date(row.RevShareDate).toLocaleDateString()}</td>
                                    <td>{Number(row.flatFeeHours).toLocaleString(undefined, { maximumFractionDigits: 1 })}</td>
                                    <td>{formatMoney(row.AverageRate)}</td>
                                    <td>{formatMoney(row.flatFeeRevenue)}</td>
                                    <td>{Number(row.HourlyHours).toLocaleString(undefined, { maximumFractionDigits: 1 })}</td>
                                    <td>{formatMoney(row.HourlyRevenue)}</td>
                                    <td>{formatMoney(row.TotalRevShareMonth)}</td>
                                    <td>{formatMoney(row.threshold)}</td>
                                    <td>{formatMoney(row.eligibleRevenue)}</td>
                                    <td>{formatMoney(row.RevTier1)}</td>
                                    <td>{formatMoney(row.RevTier2)}</td>
                                    <td>{formatMoney(row.RevTier3)}</td>
                                    <td>{formatMoney(row.productionShare)}</td>
                                    <td>{formatMoney(row.OriginationFees)}</td>
                                    <td>{formatMoney(row.RevShareTotal)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            {/* Detailed time entries hidden as per request */}
            {/* {renderTable(filteredData?.te1, "FONE Time Entries")} */}
            {/* {renderTable(filteredData?.te2, "FMON Time Entries")} */}
            {/* {renderTable(filteredData?.te3, "Hourly Time Entries")} */}

            <section className="charts-container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
                <div className="chart-section glass-card">
                    <h3>Payout Monthly Summary (Total Production Revenue)</h3>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={filteredData?.chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="month" />
                            <YAxis tickFormatter={(val) => `$${Number(val).toLocaleString()}`} />
                            <Tooltip formatter={(val) => `$${Number(val).toLocaleString()}`} />
                            <Legend />
                            <Bar dataKey="FlatFee" stackId="a" fill="#4facfe" name="Flat Fee Revenue" />
                            <Bar dataKey="Hourly" stackId="a" fill="#00f2fe" name="Hourly Revenue" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-section glass-card">
                    <h3>Top 10 Matters (Total Hours)</h3>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart layout="vertical" data={filteredData?.topClientsData} margin={{ left: 50, right: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" tickFormatter={(val) => `${Number(val).toLocaleString()}h`} />
                            <YAxis type="category" dataKey="name" width={150} />
                            <Tooltip formatter={(val) => `${Number(val).toLocaleString()} hours`} />
                            <Legend />
                            <Bar dataKey="value" fill="#64ffda" name="Total Hours" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </section>
        </div>
    );
};

export default RevShare;
