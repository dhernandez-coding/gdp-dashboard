import { useState, useEffect } from 'react';
import { getSettings, updateSettings, getPrebills, updatePrebills, getBillableHours } from '../services/api';
import './Settings.css';

const Settings = () => {
    const [settings, setSettings] = useState(null);
    const [prebills, setPrebills] = useState({});
    const [allStaff, setAllStaff] = useState([]);
    const [loading, setLoading] = useState(true);
    const [savingSettings, setSavingSettings] = useState(false);
    const [savingPrebills, setSavingPrebills] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });

    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [settingsData, prebillsData, billableHours] = await Promise.all([
                    getSettings(),
                    getPrebills(),
                    getBillableHours()
                ]);
                setSettings(settingsData);
                setPrebills(prebillsData);
                const uniqueStaff = [...new Set(billableHours.map(h => h.StaffAbbreviation))].filter(Boolean).sort();
                setAllStaff(uniqueStaff);
            } catch (err) {
                console.error('Failed to load settings:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleStaffToggle = (staff) => {
        const newStaffList = settings.custom_staff_list.includes(staff)
            ? settings.custom_staff_list.filter(s => s !== staff)
            : [...settings.custom_staff_list, staff];
        const newGoals = { ...settings.staff_weekly_goals };
        if (!newGoals[staff]) newGoals[staff] = 20;
        setSettings({ ...settings, custom_staff_list: newStaffList, staff_weekly_goals: newGoals });
    };

    const handleGoalChange = (staff, value) => {
        setSettings({ ...settings, staff_weekly_goals: { ...settings.staff_weekly_goals, [staff]: parseInt(value) || 0 } });
    };

    const saveSettings = async () => {
        try {
            setSavingSettings(true);
            const totalHours = Object.entries(settings.staff_weekly_goals)
                .filter(([staff]) => settings.custom_staff_list.includes(staff))
                .reduce((sum, [_, goal]) => sum + goal, 0);
            const updatedSettings = { ...settings, treshold_hours: totalHours };
            await updateSettings(updatedSettings);
            setSettings(updatedSettings);
            setMessage({ text: 'Settings saved successfully!', type: 'success' });
        } catch (err) {
            setMessage({ text: 'Failed to save settings', type: 'error' });
        } finally {
            setSavingSettings(false);
            setTimeout(() => setMessage({ text: '', type: '' }), 3000);
        }
    };

    const handlePrebillChange = (staff, month, value) => {
        setPrebills({ ...prebills, [staff]: { ...prebills[staff], [month]: value } });
    };

    const savePrebills = async () => {
        try {
            setSavingPrebills(true);
            await updatePrebills(prebills);
            setMessage({ text: 'Prebills saved successfully!', type: 'success' });
        } catch (err) {
            setMessage({ text: 'Failed to save prebills', type: 'error' });
        } finally {
            setSavingPrebills(false);
            setTimeout(() => setMessage({ text: '', type: '' }), 3000);
        }
    };

    if (loading) return <div className="loading-container"><div className="spinner"></div></div>;

    return (
        <div className="settings-page">
            <h1 className="page-title">🔧 Dashboard Settings</h1>
            {message.text && <div className={`alert alert-${message.type}`}>{message.text}</div>}

            <div className="settings-grid">
                <section className="settings-section card">
                    <h3>Staff Selection</h3>
                    <div className="staff-checkbox-grid">
                        {allStaff.map(staff => (
                            <label key={staff} className="checkbox-label-cell">
                                <input type="checkbox" checked={settings.custom_staff_list.includes(staff)} onChange={() => handleStaffToggle(staff)} />
                                <span>{staff}</span>
                            </label>
                        ))}
                    </div>
                </section>

                <section className="settings-section card">
                    <h3>Team Goals</h3>
                    <div className="form-group">
                        <label>Total Revenue Goal ($)</label>
                        <input type="number" className="input" value={settings.treshold_revenue} onChange={(e) => setSettings({ ...settings, treshold_revenue: parseInt(e.target.value) || 0 })} />
                    </div>
                    <p>Calculated Weekly Hours Goal: <strong>{settings.treshold_hours}</strong></p>
                    <button className="btn btn-primary" onClick={saveSettings} disabled={savingSettings}>{savingSettings ? 'Saving...' : '💾 Save Settings'}</button>
                </section>
            </div>

            <section className="settings-section card mt-4">
                <h3>Prebills Back On Time</h3>
                <div className="table-responsive">
                    <table className="prebills-table">
                        <thead>
                            <tr><th>Name</th>{months.map(m => <th key={m}>{m}</th>)}</tr>
                        </thead>
                        <tbody>
                            {settings.custom_staff_list.map(staff => (
                                <tr key={staff}>
                                    <td className="staff-name">{staff}</td>
                                    {months.map(month => (
                                        <td key={month}>
                                            <select className="prebill-select" value={prebills[staff]?.[month] || 'Yes'} onChange={(e) => handlePrebillChange(staff, month, e.target.value)}>
                                                <option value="Yes">Yes</option><option value="No">No</option>
                                            </select>
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <button className="btn btn-primary mt-3" onClick={savePrebills} disabled={savingPrebills}>{savingPrebills ? 'Saving...' : '💾 Save Prebills'}</button>
            </section>
        </div>
    );
};

export default Settings;
