// src/index.tsx

import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import { pdfjs } from 'react-pdf';

// Configure the PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `${process.env.PUBLIC_URL}/pdf.worker.min.js`;

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);
