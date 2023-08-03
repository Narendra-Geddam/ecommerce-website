// Import the required React and ReactDOM modules
import React from 'react';
import ReactDOM from 'react-dom';

// Import the main CSS file (main.min.css)
import './styles/main.min.css';

// Import the main component of the application (App)
import App from './App';

// Use ReactDOM.render() to render the App component into the DOM
ReactDOM.render(
  // Use <React.StrictMode> to enable additional checks and warnings during development
  <React.StrictMode>
    {/* Render the App component */}
    <App />
  </React.StrictMode>,
  // Specify the DOM element where the App component should be rendered (with the id 'root')
  document.getElementById('root')
);
