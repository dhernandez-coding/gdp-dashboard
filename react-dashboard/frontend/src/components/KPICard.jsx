import './KPICard.css';

const KPICard = ({ title, value, subtitle, icon }) => {
    return (
        <div className="kpi-card">
            <div className="kpi-icon-container">
                <span className="kpi-icon">{icon}</span>
            </div>
            <div className="kpi-info">
                <h3 className="kpi-title">{title}</h3>
                <p className="kpi-value">{value}</p>
                {subtitle && <p className="kpi-subtitle">{subtitle}</p>}
            </div>
        </div>
    );
};

export default KPICard;
