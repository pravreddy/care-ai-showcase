import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { isLoggedIn, logout, getUser } from '../services/api';
import { Heart, LogOut, Shield } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();
  const loggedIn = isLoggedIn();
  const user = getUser();

  const handleLogout = () => {
    logout();
    window.location.href = '/';
  };

  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
      <nav className="navbar">
        <div className="navbar-inner">
          <Link to="/" className="navbar-logo">
            <Heart size={24} />
            <span>Care AI</span>
          </Link>

          <ul className="navbar-links">
            {loggedIn ? (
                <>
                  <li><Link to="/dashboard" className={isActive('/dashboard')}>Dashboard</Link></li>
                  <li><Link to="/ask" className={isActive('/ask')}>Ask AI</Link></li>
                  <li><Link to="/notes" className={isActive('/notes')}>Notes</Link></li>
                  <li><Link to="/partner" className={isActive('/partner')}>API</Link></li>
                  <li><Link to="/docs" className={isActive('/docs')}>Docs</Link></li>
                  <li><Link to="/security" className={isActive('/security')} title="Security settings"><Shield size={16} /></Link></li>
                  <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ opacity: 0.8, fontSize: '0.85rem' }}>{user?.full_name || user?.email}</span>
                    <button onClick={handleLogout} className="btn btn-ghost btn-sm" title="Sign out">
                      <LogOut size={16} /> Sign out
                    </button>
                  </li>
                </>
            ) : (
                <>
                  <li><Link to="/try" className={isActive('/try')}>Try AI</Link></li>
                  <li><Link to="/docs" className={isActive('/docs')}>API Docs</Link></li>
                  <li><Link to="/login" className="btn btn-ghost btn-sm">Sign in</Link></li>
                  <li><Link to="/register" className="btn btn-primary btn-sm">Start free trial</Link></li>
                </>
            )}
          </ul>
        </div>
      </nav>
  );
}
