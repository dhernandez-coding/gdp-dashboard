import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const Sidebar = ({ dateRange, setDateRange, showGoals, setShowGoals, onReloadData, lastUpdate }) => {
    const { user } = useAuth();
    const allowedTabs = user?.allowed_tabs || [];

    return (
        <div className="sidebar">
            <div className="sidebar-segment">
                <h3 className="sidebar-label">Navigation</h3>
                <nav className="nav-links">
                    {allowedTabs.includes('Dashboard') && (
                        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                            RLG Dashboard
                        </NavLink>
                    )}
                    {allowedTabs.includes('RevShare') && (
                        <NavLink to="/revshare" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                            Revenue Share
                        </NavLink>
                    )}
                    {allowedTabs.includes('Settings') && (
                        <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                            Settings
                        </NavLink>
                    )}
                </nav>
            </div>

            <div className="sidebar-segment">
                <h3 className="sidebar-label">Filters</h3>
                <div className="filter-group">
                    <label>Start Date</label>
                    <input
                        type="date"
                        className="input sidebar-input"
                        value={dateRange.start}
                        onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                    />
                </div>
                <div className="filter-group">
                    <label>End Date</label>
                    <input
                        type="date"
                        className="input sidebar-input"
                        value={dateRange.end}
                        onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                    />
                </div>
                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={showGoals}
                        onChange={(e) => setShowGoals(e.target.checked)}
                    />
                    Show Goal Lines
                </label>
            </div>

            <div className="sidebar-segment mt-auto">
                <button className="btn btn-primary w-full" onClick={onReloadData}>Reload Data</button>
                {lastUpdate && <p className="last-update">Last update: {new Date(lastUpdate).toLocaleString()}</p>}
            </div>
        </div>
    );
};

export default Sidebar;
