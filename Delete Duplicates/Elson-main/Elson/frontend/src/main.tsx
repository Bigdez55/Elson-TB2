import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter as Router } from 'react-router-dom'
import App from './app/components/layout/App'
import { store } from './app/store/store'
import { initPWA } from './pwa-config'
import * as serviceWorkerRegistration from './serviceWorkerRegistration';
import './styles/global.css'

// Initialize Progressive Web App features
initPWA();

// Register service worker for PWA capabilities
serviceWorkerRegistration.register({
  onUpdate: (registration) => {
    serviceWorkerRegistration.displayUpdateNotification(registration);
  }
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider store={store}>
      <Router>
        <App />
      </Router>
    </Provider>
  </React.StrictMode>,
)