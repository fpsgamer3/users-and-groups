import React, { useState, useEffect } from 'react';
import './App.css';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import GroupPage from './components/GroupPage';
import LoadingAnimation from './components/LoadingAnimation';
import { LanguageProvider } from './LanguageContext';
import { useLanguage } from './LanguageContext';
import { getCsrfToken } from './utils/csrf';

function App() {
  const [page, setPage] = useState('login'); // 'login' or 'register'
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAnimation, setShowAnimation] = useState(false);
  const [animationDirection, setAnimationDirection] = useState('clockwise');

  // Helper to re-check session state
  const recheckSession = async () => {
    console.log('Re-checking session...');
    try {
      const response = await fetch('http://localhost:8000/api/auth/current-user/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        const userData = data.user || data;
        if (userData && userData.id) {
          setUser(userData);
          setPage('groups');
          return true;
        }
      }
    } catch (err) {
      console.error('Error re-checking session:', err);
    }

    setUser(null);
    setPage('login');
    return false;
  };

  // Check if user is already logged in when app loads
  useEffect(() => {
    (async () => {
      await recheckSession();
      setLoading(false);
    })();
  }, []);

  // Listen for auth changes from other tabs/windows or when tab becomes visible
  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === 'auth-event') {
        console.log('Received auth-event from another tab:', e.newValue);
        recheckSession();
      }
    };

    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        // When tab becomes active, directly re-check session
        recheckSession();
      }
    };

    window.addEventListener('storage', handleStorage);
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
      window.removeEventListener('storage', handleStorage);
      document.removeEventListener('visibilitychange', handleVisibility);
    };
  }, []);

  const handleUserLogin = (userData) => {
    if (userData === 'REGISTER_PAGE') {
      setPage('register');
    } else if (userData) {
      setShowAnimation(true);
      setAnimationDirection('clockwise');
      setUser(userData);
      setTimeout(() => {
        setPage('groups');
        setShowAnimation(false);
      }, 1300);
      // Broadcast login to other tabs
      try {
        localStorage.setItem('auth-event', JSON.stringify({ type: 'login', ts: Date.now() }));
      } catch (e) {
        console.warn('Could not write auth-event to localStorage', e);
      }
    } else {
      setPage('login');
    }
  };

  const handleRegistrationSuccess = (userData) => {
    setPage('login');
  };

  const handleLogout = () => {
    // Call backend logout to clear session cookie, then clear local state
    const doLogout = async () => {
      setShowAnimation(true);
      setAnimationDirection('counter-clockwise');
      try {
        const csrfToken = getCsrfToken();
        const headers = {
          'Content-Type': 'application/json',
        };
        if (csrfToken) headers['X-CSRFToken'] = csrfToken;

        await fetch('http://localhost:8000/api/auth/logout/', {
          method: 'POST',
          headers,
          credentials: 'include',
        });
      } catch (err) {
        console.error('Error during logout:', err);
      } finally {
        setTimeout(() => {
          setUser(null);
          setPage('login');
          setShowAnimation(false);
          try {
            localStorage.setItem('auth-event', JSON.stringify({ type: 'logout', ts: Date.now() }));
          } catch (e) {
            console.warn('Could not write auth-event to localStorage', e);
          }
        }, 1300);
      }
    };

    doLogout();
  };

  if (loading) {
    return (
      <LanguageProvider>
        <div className="App"><p>Loading...</p></div>
      </LanguageProvider>
    );
  }

  return (
    <LanguageProvider>
      <div className="App">
        {showAnimation && <LoadingAnimation direction={animationDirection} />}
        {page === 'groups' ? (
          <GroupPage user={user} onLogout={handleLogout} />
        ) : page === 'login' ? (
          <LoginPage onUserLogin={handleUserLogin} initialUser={user} onLogout={handleLogout} />
        ) : (
          <RegisterPage onRegistrationSuccess={handleRegistrationSuccess} />
        )}
      </div>
    </LanguageProvider>
  );
}

export default App;
