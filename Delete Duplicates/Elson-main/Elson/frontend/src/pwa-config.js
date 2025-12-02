/**
 * Progressive Web App configuration for Elson Wealth Management
 * This file configures service worker and PWA features
 */

// Define the service worker registration logic
export const registerServiceWorker = async () => {
  if ('serviceWorker' in navigator) {
    try {
      const registration = await navigator.serviceWorker.register('/service-worker.js', {
        scope: '/'
      });
      
      if (registration.installing) {
        console.log('Service worker installing');
      } else if (registration.waiting) {
        console.log('Service worker installed but waiting');
      } else if (registration.active) {
        console.log('Service worker active');
      }
      
      // Handle updates to the service worker
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New content is available, notify the user
            dispatchEvent(new CustomEvent('pwa-update-available'));
          }
        });
      });
      
      return registration;
    } catch (error) {
      console.error('Service worker registration failed:', error);
    }
  }
};

// Check for PWA installation eligibility
export const checkInstallEligibility = () => {
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return { eligible: false, reason: 'already-installed' };
  }
  
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
  
  if (isIOS && !isSafari) {
    return { eligible: false, reason: 'ios-not-safari' };
  }
  
  if (!('serviceWorker' in navigator)) {
    return { eligible: false, reason: 'no-service-worker-support' };
  }
  
  return { eligible: true };
};

// Handle the install prompt
let deferredPrompt;

export const initInstallPrompt = () => {
  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67+ from automatically showing the prompt
    e.preventDefault();
    
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Notify that installation is available
    dispatchEvent(new CustomEvent('pwa-installable'));
  });
  
  // Detect when PWA is installed
  window.addEventListener('appinstalled', () => {
    // Log install to analytics
    console.log('PWA was installed');
    deferredPrompt = null;
    
    // Notify that installation is complete
    dispatchEvent(new CustomEvent('pwa-installed'));
  });
};

// Show the installation prompt
export const showInstallPrompt = async () => {
  if (!deferredPrompt) {
    console.log('No installation prompt available');
    return false;
  }
  
  // Show the install prompt
  deferredPrompt.prompt();
  
  // Wait for the user to respond to the prompt
  const result = await deferredPrompt.userChoice;
  
  // We no longer need the prompt
  deferredPrompt = null;
  
  // Return true if the user accepted the installation
  return result.outcome === 'accepted';
};

// Configure offline detection and notification
export const initOfflineDetection = () => {
  window.addEventListener('online', () => {
    dispatchEvent(new CustomEvent('pwa-online'));
  });
  
  window.addEventListener('offline', () => {
    dispatchEvent(new CustomEvent('pwa-offline'));
  });
  
  // Initial check
  if (!navigator.onLine) {
    dispatchEvent(new CustomEvent('pwa-offline'));
  }
};

// Initialize PWA features
export const initPWA = () => {
  registerServiceWorker();
  initInstallPrompt();
  initOfflineDetection();
};

export default {
  registerServiceWorker,
  checkInstallEligibility,
  initInstallPrompt,
  showInstallPrompt,
  initOfflineDetection,
  initPWA
};