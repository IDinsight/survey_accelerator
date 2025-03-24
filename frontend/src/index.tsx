import React from 'react';
import ReactDOM from 'react-dom';
import { Auth0Provider } from '@auth0/auth0-react';
import App from './App';
import './index.css';


ReactDOM.render(
  <React.StrictMode>  
    <Auth0Provider
    domain="dev-7ta1du6edpr2dv1o.us.auth0.com"
    clientId="Ps4L57Hno5d6d0o93JBTeXd33RF3TrpW"
    authorizationParams={{
      redirect_uri: 'http://localhost:3000',
    }}
  >
      <App />
  </Auth0Provider>
  </React.StrictMode>,
  document.getElementById('root')

);
