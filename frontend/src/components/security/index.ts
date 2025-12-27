// Security Management Components
export { default as SecurityDashboard } from './SecurityDashboard';
export { default as DeviceManagement } from './DeviceManagement';
export { default as TwoFactorAuth } from './TwoFactorAuth';
export { default as SecuritySettings } from './SecuritySettings';
export { default as BiometricSetup } from './BiometricSetup';
export { default as BiometricAuth } from './BiometricAuth';
export { default as BiometricManagement } from './BiometricManagement';

// Re-export types for convenience
export type {
  DeviceInfo,
  SecuritySession,
  TwoFactorConfig,
  LoginAttempt,
  SecurityAlert,
  SecuritySettings as SecuritySettingsType,
  DeviceRegistrationRequest,
  DeviceVerificationRequest,
  SessionTerminationRequest,
} from '../../services/deviceManagementApi';