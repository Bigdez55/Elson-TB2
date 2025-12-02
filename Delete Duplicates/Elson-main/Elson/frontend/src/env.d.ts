/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Base URLs
  readonly VITE_API_URL: string | undefined;
  readonly VITE_WEBSOCKET_URL: string | undefined;
  
  // Feature flags
  readonly VITE_ENABLE_ANALYTICS: string | undefined;
  readonly VITE_ENABLE_MOCK_DATA: string | undefined;
  
  // Application config
  readonly VITE_APP_NAME: string | undefined;
  readonly VITE_APP_VERSION: string | undefined;
  readonly VITE_ENVIRONMENT: string | undefined;
  
  // API Keys (for public client-side APIs only)
  readonly VITE_PUBLIC_STRIPE_KEY: string | undefined;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}