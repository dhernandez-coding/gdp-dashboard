
import React, { useEffect, useState } from 'react';
import './NotificationToast.css';

const NotificationToast = ({ notifications, onClose }) => {
    const [visible, setVisible] = useState(true);

    if (!notifications || notifications.length === 0 || !visible) {
        return null;
    }

    const handleClose = () => {
        setVisible(false);
        setTimeout(() => {
            if (onClose) onClose();
        }, 300);
    };

    return (
        <div className="notification-container">
            <div className={`notification-toast ${!visible ? 'closing' : ''}`}>
                <div className="notification-header">
                    <span className="notification-title">
                        ⚠️ Budget Alert
                    </span>
                    <button className="notification-close" onClick={handleClose}>
                        &times;
                    </button>
                </div>
                <div className="notification-body">
                    <p>The following matters have exceeded 80% of their budget:</p>
                    <div className="notification-list">
                        {notifications.map((n) => (
                            <div key={n.id} className="matter-item">
                                <span className="matter-name">{n.matter_name}</span>
                                <div className="matter-details">
                                    <span>Used: {n.percent_used}%</span>
                                    <span>${n.burned_amount?.toLocaleString() || 0} / ${n.budget?.toLocaleString() || 0}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NotificationToast;
