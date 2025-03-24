// src/App.tsx
import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import AdvancedSearchEngine from './AdvancedSearchEngine';
import LoginButton from './components/Login';
import LogoutButton from './components/Logout';
import './App.css';

const App: React.FC = () => {
  const { isLoading, error, isAuthenticated } = useAuth0();

  if (error) {
    console.error(error);
    return <div>Authentication Error</div>;
  }

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <>
      {isAuthenticated ? (
        <AdvancedSearchEngine />
      ) : (
        <div className="login-container">
          <LoginButton />
          <p>Please log in to access the Advanced Search Engine.</p>
        </div>
      )}
    </>
  );
};

export default App;
