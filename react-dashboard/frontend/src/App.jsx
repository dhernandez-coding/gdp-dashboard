import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { getAllData, getSettings } from './services/api';

// Components
import Header from './components/Header';
import Sidebar from './components/Sidebar';

// Pages
import Login from './pages/Login';
import RLGDashboard from './pages/RLGDashboard';
import RevShare from './pages/RevShare';
import Settings from './pages/Settings';

import './App.css';

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();

    if (loading) return <div className="loading-container"><div className="spinner"></div></div>;
    if (!isAuthenticated) return <Navigate to="/login" />;

    return children;
};

function App() {
    const { user } = useAuth();
    const [data, setData] = useState(null);
    const [settings, setSettings] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showGoals, setShowGoals] = useState(true);
    const [dateRange, setDateRange] = useState({
        start: new Date(new Date().setFullYear(new Date().getFullYear() - 1)).toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
    });

    const fetchData = async () => {
        try {
            setLoading(true);
            const [allData, settingsData] = await Promise.all([
                getAllData(),
                getSettings()
            ]);
            setData(allData);
            setSettings(settingsData);
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (user) {
            fetchData();
        }
    }, [user]);

    if (loading && user) {
        return <div className="loading-container"><div className="spinner"></div></div>;
    }

    return (
        <div className="app">
            <Routes>
                <Route path="/login" element={<Login />} />

                <Route
                    path="*"
                    element={
                        <ProtectedRoute>
                            <div className="layout">
                                <Header />
                                <div className="main-wrapper">
                                    <Sidebar
                                        dateRange={dateRange}
                                        setDateRange={setDateRange}
                                        showGoals={showGoals}
                                        setShowGoals={setShowGoals}
                                        onReloadData={fetchData}
                                        lastUpdate={data?.last_update}
                                    />
                                    <main className="content">
                                        <Routes>
                                            <Route path="/" element={
                                                <RLGDashboard
                                                    data={data}
                                                    dateRange={dateRange}
                                                    showGoals={showGoals}
                                                    settings={settings}
                                                />
                                            } />
                                            <Route path="/revshare" element={<RevShare settings={settings} dateRange={dateRange} />} />
                                            <Route path="/settings" element={<Settings />} />
                                        </Routes>
                                    </main>
                                </div>
                            </div>
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </div>
    );
}

export default App;
