import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
// Azure Web Apps uses the PORT environment variable
const PORT = process.env.PORT || 8080;
// Note: This expects your backend to run on Azure Web Apps or another URL
const BACKEND_URL = process.env.BACKEND_URL || 'https://rlgokcbackend.azurewebsites.net';

// Proxy all requests starting with /api to the backend
app.use('/api', createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
}));

// Serve static files from the Vite build output directory
app.use(express.static(path.join(__dirname, 'dist')));

// Fallback to index.html for React Router
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist/index.html'));
});

app.listen(PORT, () => {
    console.log(`Frontend production server listening on port ${PORT}`);
    console.log(`Proxying /api requests to ${BACKEND_URL}`);
});
