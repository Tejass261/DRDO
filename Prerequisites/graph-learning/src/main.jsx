import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

// Grab the 'root' div from index.html and inject the React app inside it
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);