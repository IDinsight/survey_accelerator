// src/App.tsx
import React, { useState } from 'react';
import AdvancedSearchEngine from './AdvancedSearchEngine';
import AuthPage from './auth/AuthPage';
import './App.css';

interface User {
  email: string;
  // Add additional fields as needed.
}

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);

  // Called by AuthPage on successful login/registration.
  const handleLoginSuccess = (userData: User) => {
    setUser(userData);
  };

  // Optionally, pass a logout function to your advanced app.
  const handleLogout = () => {
    setUser(null);
  };

  return (
    <>
      {user ? (
        // You can pass the user object or logout callback if needed.
        <AdvancedSearchEngine />
      ) : (
        <AuthPage onLoginSuccess={handleLoginSuccess} />
      )}
    </>
  );
};

export default App;
