import React, { useState, useEffect } from 'react';
import './LoginPage.css';
import { getCsrfToken } from '../utils/csrf';

function LoginPage({ onUserLogin, initialUser, onLogout }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(initialUser || null);

  console.log('LoginPage rendered. initialUser:', initialUser, 'user state:', user);

  useEffect(() => {
    if (initialUser) {
      console.log('useEffect: Setting user from initialUser:', initialUser);
      setUser(initialUser);
    }
  }, [initialUser]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const csrfToken = getCsrfToken();
      
      const headers = {
        'Content-Type': 'application/json',
      };
      
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      const response = await fetch('http://localhost:8000/api/auth/login/', {
        method: 'POST',
        headers: headers,
        credentials: 'include',
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.non_field_errors ? data.non_field_errors[0] : 'Login failed');
      }

      const data = await response.json();
      console.log('Login successful! Response:', data);
      console.log('Setting user:', data.user);
      setUser(data.user);
      setUsername('');
      setPassword('');
      onUserLogin(data.user);  // Notify parent that login was successful
    } catch (err) {
      setError(err.message || 'An error occurred during login');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      const csrfToken = getCsrfToken();
      const headers = {
        'Content-Type': 'application/json',
      };
      
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }

      await fetch('http://localhost:8000/api/auth/logout/', {
        method: 'POST',
        headers: headers,
        credentials: 'include',
      });
    } catch (err) {
      console.error('Logout error:', err);
    }
    
    setUser(null);
    setUsername('');
    setPassword('');
    if (onLogout) {
      onLogout();
    }
  };

  const handleRegisterClick = () => {
    // Signal parent to go to register page
    onUserLogin('REGISTER_PAGE');
  };

  return (
    <div className="login-container">
      {!user ? (
        <div className="login-card">
          <div className="login-logo">
            <img src="/logo.png" alt="Leav Logo" />
            <h1>Leav</h1>
            <p>Login to your account</p>
          </div>

          {error && <div className="login-error">{error}</div>}

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>

            <button className="btn-login" type="submit" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="demo-credentials">
            <p><strong>Demo Credentials:</strong></p>
            <p>Teacher: john_doe / teacher123</p>
            <p>Student: alice_student / student123</p>
            <p>Admin: admin / admin123</p>
          </div>

          <div className="login-footer">
            <p>Not a user? <span className="register-link" onClick={handleRegisterClick}>Create account here</span></p>
          </div>
        </div>
      ) : (
        <div className="success-card">
          <div className="success-message">
            <h2>✓ You are logged in</h2>
            <p>Welcome, {user.first_name || user.username}!</p>
            <p className="role-label">Your role is:</p>
            <div className="role-badge">
              {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
            </div>
          </div>

          <div className="user-info">
            <p><strong>Username:</strong> {user.username}</p>
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Full Name:</strong> {user.first_name} {user.last_name}</p>
            <p><strong>Role:</strong> {user.role}</p>
          </div>

          <button className="btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      )}
    </div>
  );
}

export default LoginPage;
