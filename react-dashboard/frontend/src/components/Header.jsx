import { useAuth } from '../context/AuthContext';
import './Header.css';

const Header = () => {
    const { user, logout } = useAuth();

    return (
        <header className="header">
            <div className="header-left">
                <h2 className="header-title">RLG Dashboard</h2>
            </div>
            <div className="header-right">
                <span className="user-welcome">Welcome, {user?.username}</span>
                <button className="btn btn-logout" onClick={logout}>Logout</button>
            </div>
        </header>
    );
};

export default Header;
