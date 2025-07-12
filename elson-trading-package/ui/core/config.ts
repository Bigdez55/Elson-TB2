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
  
  // Determine API URL - REQUIRED for production
  const apiUrl = import.meta.env.VITE_API_URL || (
    environment === Environment.DEVELOPMENT 
      ? 'http://localhost:8000/api/v1'
      : ''
  );
  
  // Determine WebSocket URL - REQUIRED for production
  const websocketUrl = import.meta.env.VITE_WEBSOCKET_URL || (
    environment === Environment.DEVELOPMENT
      ? 'ws://localhost:8000'
      : ''
  );
  
  // Validate required configuration for production/staging
  if (environment !== Environment.DEVELOPMENT) {
    if (!apiUrl) {
      throw new Error(`VITE_API_URL must be set for ${environment} environment`);
    }
    if (!websocketUrl) {
      throw new Error(`VITE_WEBSOCKET_URL must be set for ${environment} environment`);
    }
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