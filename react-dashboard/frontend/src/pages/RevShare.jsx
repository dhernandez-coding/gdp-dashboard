import { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getRevShareData } from '../services/api';
import KPICard from '../components/KPICard';
import './RevShare.css';

const RevShare = ({ settings, dateRange }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedStaff, setSelectedStaff] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const result = await getRevShareData();
                setData(result);
                if (settings?.custom_staff_list?.length > 0) {
                    setSelectedStaff(settings.custom_staff_list[0]);
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
                return date >= startDate && date <= endDate && item.Staff === selectedStaff;
            });
        };

        const revShare = filterByDateAndStaff(data.revshare, 'RevShareDate');
        const te1 = filterByDateAndStaff(data.te_type1, 'TimeEntryDate');
        const te2 = filterByDateAndStaff(data.te_type2, 'TimeEntryDate');
        const te3 = filterByDateAndStaff(data.te_type3, 'TimeEntryDate');

        const totalProductionRevenue = revShare.reduce((sum, item) => sum + (item.TotalRevShareMonth || 0), 0);
        const totalRevenueShare = revShare.reduce((sum, item) => sum + (item.RevShareTotal || 0), 0);
        const totalHours = [...te1, ...te2, ...te3].reduce((sum, item) => sum + (item.TimeEntryAmount || 0), 0);

        const payoutByMonth = {};
        const processTE = (list, type) => {
            list.forEach(item => {
                const month = new Date(item.TimeEntryDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                if (!payoutByMonth[month]) payoutByMonth[month] = { month, FONE: 0, FMON: 0, Hourly: 0 };
                payoutByMonth[month][type] += (item.TotalPayout || 0);
            });
        };

        processTE(te1, 'FONE');
        processTE(te2, 'FMON');
        processTE(te3, 'Hourly');

        const chartData = Object.values(payoutByMonth).sort((a, b) => new Date(a.month) - new Date(b.month));

        return { totalProductionRevenue, totalRevenueShare, totalHours, chartData, revShare, te1, te2, te3 };
    }, [data, selectedStaff, dateRange]);

    if (loading) return <div className="loading-container"><div className="spinner"></div></div>;
    if (error) return <div className="error-message">{error}</div>;

    const staffList = settings?.custom_staff_list || [];

    return (
        <div className="revshare-page">
            <div className="page-header">
                <h1 className="page-title">Revenue Share Review</h1>
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
            </div>

            <div className="kpi-grid">
                <KPICard title="Total Production Revenue" value={`$${filteredData?.totalProductionRevenue.toLocaleString()}`} icon="💰" />
                <KPICard title="Total Hours" value={`${filteredData?.totalHours.toLocaleString()} hours`} icon="⏱️" />
                <KPICard title="Total Revenue Share" value={`$${filteredData?.totalRevenueShare.toLocaleString()}`} icon="💸" />
            </div>

            <section className="chart-section card mt-4">
                <h3>Payout Summary for {selectedStaff}</h3>
                <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={filteredData?.chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis tickFormatter={(val) => `$${val.toLocaleString()}`} />
                        <Tooltip formatter={(val) => `$${val.toLocaleString()}`} />
                        <Legend />
                        <Bar dataKey="FONE" fill="#052B48" />
                        <Bar dataKey="FMON" fill="#3371A1" />
                        <Bar dataKey="Hourly" fill="#4CA7ED" />
                    </BarChart>
                </ResponsiveContainer>
            </section>

            <section className="table-section card mt-4">
                <h3>Revenue Share Summary</h3>
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Year</th><th>Month</th><th>Staff</th>
                                <th>FONE Hours</th><th>FONE Revenue</th>
                                <th>FMON Hours</th><th>FMON Revenue</th>
                                <th>Hourly Hours</th><th>Hourly Revenue</th>
                                <th>Total Production</th><th>Total Share</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredData?.revShare.map((row, i) => (
                                <tr key={i}>
                                    <td>{row.RevShareYear}</td><td>{row.RevShareMonth}</td><td>{row.Staff}</td>
                                    <td>{row.FONEHours?.toFixed(1)}</td><td>${row.FONERevenue?.toLocaleString()}</td>
                                    <td>{row.FMONHours?.toFixed(1)}</td><td>${row.FMONRevenue?.toLocaleString()}</td>
                                    <td>{row.HourlyHours?.toFixed(1)}</td><td>${row.HourlyRevenue?.toLocaleString()}</td>
                                    <td>${row.TotalRevShareMonth?.toLocaleString()}</td><td>${row.RevShareTotal?.toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
};

export default RevShare;
