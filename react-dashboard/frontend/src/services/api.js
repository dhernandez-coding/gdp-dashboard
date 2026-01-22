import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to attach the JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('rlg_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Add a response interceptor to handle unauthorized errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('rlg_token');
            localStorage.removeItem('rlg_user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Authentication
export const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
};

export const verifyToken = async () => {
    const response = await api.get('/auth/verify');
    return response.data;
};

// Data
export const getAllData = async () => {
    const response = await api.get('/data/all');
    return response.data;
};

export const getRevenue = async () => {
    const response = await api.get('/data/revenue');
    return response.data;
};

export const getBillableHours = async () => {
    const response = await api.get('/data/billable-hours');
    return response.data;
};

export const getMatters = async () => {
    const response = await api.get('/data/matters');
    return response.data;
};

export const getRevShareData = async () => {
    const response = await api.get('/data/revshare');
    return response.data;
};

// Settings & Prebills
export const getSettings = async () => {
    const response = await api.get('/settings');
    return response.data;
};

export const updateSettings = async (settings) => {
    const response = await api.put('/settings', settings);
    return response.data;
};

export const getPrebills = async () => {
    const response = await api.get('/prebills');
    return response.data;
};

export const updatePrebills = async (prebills) => {
    const response = await api.put('/prebills', prebills);
    return response.data;
};

export default api;
