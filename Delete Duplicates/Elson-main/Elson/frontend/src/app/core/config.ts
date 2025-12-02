/**
 * Application configuration
 * Centralized access to environment variables and configuration settings
 */

// Environment types
export enum Environment {
  DEVELOPMENT = 'development',
  STAGING = 'staging',
  PRODUCTION = 'production'
}

// Configuration interface
interface AppConfig {
  // API and service URLs
  apiUrl: string;
  websocketUrl: string;
  
  // Environment settings
  environment: Environment;
  isDev: boolean;
  isProd: boolean;
  isStaging: boolean;
  
  // Feature flags
  enableAnalytics: boolean;
  enableMockData: boolean;
  
  // Application metadata
  appName: string;
  appVersion: string;
  
  // External service keys (public only)
  stripePubKey: string;
}

/**
 * Determine current environment
 */
const determineEnvironment = (): Environment => {
  const envValue = import.meta.env.VITE_ENVIRONMENT?.toLowerCase();
  
  if (envValue === 'production') {
    return Environment.PRODUCTION;
  } else if (envValue === 'staging') {
    return Environment.STAGING;
  }
  
  // Default to development
  return Environment.DEVELOPMENT;
};

/**
 * Build configuration from environment variables
 */
const buildConfig = (): AppConfig => {
  const environment = determineEnvironment();
  
  // Determine API URL
  let apiUrl = import.meta.env.VITE_API_URL;
  if (!apiUrl) {
    apiUrl = environment === Environment.PRODUCTION
      ? 'https://api.elsonwealth.com/api/v1'
      : 'http://localhost:8000/api/v1';
  }
  
  // Determine WebSocket URL
  let websocketUrl = import.meta.env.VITE_WEBSOCKET_URL;
  if (!websocketUrl) {
    websocketUrl = environment === Environment.PRODUCTION
      ? 'wss://api.elsonwealth.com'
      : 'ws://localhost:8000';
  }
  
  return {
    // API and service URLs
    apiUrl,
    websocketUrl,
    
    // Environment settings
    environment,
    isDev: environment === Environment.DEVELOPMENT,
    isProd: environment === Environment.PRODUCTION,
    isStaging: environment === Environment.STAGING,
    
    // Feature flags
    enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
    enableMockData: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true',
    
    // Application metadata
    appName: import.meta.env.VITE_APP_NAME || 'Elson Wealth',
    appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
    
    // External service keys
    stripePubKey: import.meta.env.VITE_PUBLIC_STRIPE_KEY || '',
  };
};

// Export the configuration
const config: AppConfig = buildConfig();
export default config;