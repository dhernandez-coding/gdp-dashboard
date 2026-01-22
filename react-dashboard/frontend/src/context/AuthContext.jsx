import { createContext, useState, useContext, useEffect } from 'react';
import { login as apiLogin, verifyToken } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem('rlg_token');
            const savedUser = localStorage.getItem('rlg_user');

            if (token && savedUser) {
                try {
                    setUser(JSON.parse(savedUser));
                    // Verify token in background
                    const userData = await verifyToken();
                    setUser(userData);
                    localStorage.setItem('rlg_user', JSON.stringify(userData));
                } catch (error) {
                    console.error('Auth verification failed', error);
                    logout();
                }
            }
            setLoading(false);
        };

        checkAuth();
    }, []);

    const jsonParse = (str) => {
        try {
            return JSON.parse(str);
        } catch {
            return null;
        }
    };

    const login = async (email, password) => {
        const data = await apiLogin(email, password);
        localStorage.setItem('rlg_token', data.token);
        localStorage.setItem('rlg_user', JSON.stringify(data.user));
        setUser(data.user);
        return data.user;
    };

    const logout = () => {
        localStorage.removeItem('rlg_token');
        localStorage.removeItem('rlg_user');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
