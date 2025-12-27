import React, { useState } from 'react';
import {
  useGetTwoFactorConfigQuery,
  useEnable2FAMutation,
  useVerify2FAMutation,
  useDisable2FAMutation,
  useRegenerateBackupCodesMutation,
  TwoFactorConfig,
} from '../../services/deviceManagementApi';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface TwoFactorAuthProps {
  className?: string;
}

interface SetupStepProps {
  step: number;
  title: string;
  children: React.ReactNode;
  isActive: boolean;
  isCompleted: boolean;
}

const SetupStep: React.FC<SetupStepProps> = ({ step, title, children, isActive, isCompleted }) => {
  return (
    <div className={`border rounded-lg p-4 ${isActive ? 'border-purple-500 bg-purple-900 bg-opacity-20' : 'border-gray-600 bg-gray-700'}`}>
      <div className="flex items-center space-x-3 mb-3">
        <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
          isCompleted ? 'bg-green-600 text-white' : 
          isActive ? 'bg-purple-600 text-white' : 
          'bg-gray-600 text-gray-300'
        }`}>
          {isCompleted ? '✓' : step}
        </div>
        <h4 className="text-white font-medium">{title}</h4>
      </div>
      {(isActive || isCompleted) && (
        <div className="ml-11">
          {children}
        </div>
      )}
    </div>
  );
};

export const TwoFactorAuth: React.FC<TwoFactorAuthProps> = ({ className = '' }) => {
  const [setupMode, setSetupMode] = useState<'totp' | 'sms' | 'email' | null>(null);
  const [setupStep, setSetupStep] = useState(1);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [disableVerificationCode, setDisableVerificationCode] = useState('');

  // API hooks
  const { data: config, isLoading, refetch } = useGetTwoFactorConfigQuery();
  const [enable2FA, { isLoading: isEnabling }] = useEnable2FAMutation();
  const [verify2FA, { isLoading: isVerifying }] = useVerify2FAMutation();
  const [disable2FA, { isLoading: isDisabling }] = useDisable2FAMutation();
  const [regenerateBackupCodes, { isLoading: isRegenerating }] = useRegenerateBackupCodesMutation();

  const handleStartSetup = async (method: 'totp' | 'sms' | 'email') => {
    try {
      setSetupMode(method);
      setSetupStep(1);
      
      const identifier = method === 'sms' ? phoneNumber : method === 'email' ? email : undefined;
      const result = await enable2FA({ method, identifier }).unwrap();
      
      if (method === 'totp' && result.qr_code) {
        setQrCode(result.qr_code);
      }
      
      setSetupStep(2);
    } catch (error) {
      console.error('Failed to start 2FA setup:', error);
      alert('Failed to start 2FA setup');
    }
  };

  const handleVerifySetup = async () => {
    if (!setupMode || !verificationCode) return;
    
    try {
      const result = await verify2FA({ 
        code: verificationCode, 
        method: setupMode 
      }).unwrap();
      
      if (result.backup_codes) {
        setBackupCodes(result.backup_codes);
        setShowBackupCodes(true);
      }
      
      setSetupStep(3);
      refetch();
    } catch (error) {
      console.error('Failed to verify 2FA setup:', error);
      alert('Invalid verification code. Please try again.');
    }
  };

  const handleDisable2FA = async () => {
    if (!disableVerificationCode) {
      alert('Please enter a verification code to disable 2FA');
      return;
    }

    if (!window.confirm('Are you sure you want to disable two-factor authentication? This will reduce your account security.')) {
      return;
    }

    try {
      await disable2FA({
        verification_code: disableVerificationCode,
        method: config?.methods[0]?.type || 'totp'
      }).unwrap();
      
      refetch();
      setDisableVerificationCode('');
      alert('Two-factor authentication has been disabled');
    } catch (error) {
      console.error('Failed to disable 2FA:', error);
      alert('Failed to disable 2FA. Please check your verification code.');
    }
  };

  const handleRegenerateBackupCodes = async () => {
    if (!window.confirm('Are you sure you want to regenerate backup codes? Your current codes will become invalid.')) {
      return;
    }

    try {
      const result = await regenerateBackupCodes({
        verification_code: disableVerificationCode
      }).unwrap();
      
      setBackupCodes(result.backup_codes);
      setShowBackupCodes(true);
    } catch (error) {
      console.error('Failed to regenerate backup codes:', error);
      alert('Failed to regenerate backup codes. Please check your verification code.');
    }
  };

  const resetSetup = () => {
    setSetupMode(null);
    setSetupStep(1);
    setQrCode(null);
    setVerificationCode('');
    setBackupCodes([]);
    setShowBackupCodes(false);
  };

  const downloadBackupCodes = () => {
    const content = backupCodes.join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'elson-trading-backup-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <LoadingSpinner size="md" />
        <span className="ml-3 text-gray-400">Loading security settings...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Current Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">Two-Factor Authentication</h3>
          <Badge 
            variant={config?.is_enabled ? 'success' : 'warning'} 
            size="sm"
          >
            {config?.is_enabled ? 'Enabled' : 'Disabled'}
          </Badge>
        </div>
        
        <p className="text-gray-400 text-sm mb-4">
          Add an extra layer of security to your account by requiring a second form of authentication.
        </p>

        {config?.is_enabled ? (
          <div className="space-y-4">
            {/* Enabled Methods */}
            <div>
              <h4 className="text-white font-medium mb-2">Active Methods</h4>
              <div className="space-y-2">
                {config.methods.map((method, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-700 rounded p-3">
                    <div className="flex items-center space-x-3">
                      <div className="text-gray-400">
                        {method.type === 'totp' && (
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 1.182C4.77 15.916 3 13.658 3 11c0-4.418 4.03-8 9-8s9 3.582 9 8c0 2.658-1.77 4.916-3 7.182" />
                          </svg>
                        )}
                        {method.type === 'sms' && (
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M8 21h8a1 1 0 001-1V4a1 1 0 00-1-1H8a1 1 0 00-1 1v16a1 1 0 001 1z" />
                          </svg>
                        )}
                        {method.type === 'email' && (
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                        )}
                      </div>
                      <div>
                        <div className="text-white text-sm font-medium">
                          {method.type === 'totp' ? 'Authenticator App' : 
                           method.type === 'sms' ? 'SMS' : 'Email'}
                        </div>
                        <div className="text-gray-400 text-xs">
                          {method.identifier}
                          {method.is_primary && (
                            <Badge variant="info" size="sm" className="ml-2">Primary</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <Badge 
                      variant={method.verified ? 'success' : 'warning'} 
                      size="sm"
                    >
                      {method.verified ? 'Verified' : 'Pending'}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>

            {/* Backup Codes */}
            <div className="bg-gray-700 rounded p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white text-sm font-medium">Backup Codes</span>
                <span className="text-gray-400 text-xs">
                  {config.backup_codes_count} remaining
                </span>
              </div>
              <p className="text-gray-400 text-xs mb-3">
                Use these codes if you lose access to your primary 2FA method.
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="password"
                  placeholder="Enter 2FA code to manage backup codes"
                  value={disableVerificationCode}
                  onChange={(e) => setDisableVerificationCode(e.target.value)}
                  className="bg-gray-600 border border-gray-500 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-purple-500"
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleRegenerateBackupCodes}
                  disabled={!disableVerificationCode || isRegenerating}
                >
                  {isRegenerating ? <LoadingSpinner size="xs" /> : 'Regenerate'}
                </Button>
              </div>
            </div>

            {/* Disable 2FA */}
            <div className="bg-red-900 bg-opacity-20 border border-red-700 rounded p-4">
              <h4 className="text-red-300 font-medium mb-2">Disable Two-Factor Authentication</h4>
              <p className="text-red-400 text-sm mb-3">
                Disabling 2FA will reduce your account security.
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="password"
                  placeholder="Enter 2FA code to disable"
                  value={disableVerificationCode}
                  onChange={(e) => setDisableVerificationCode(e.target.value)}
                  className="bg-gray-600 border border-gray-500 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-purple-500"
                />
                <Button
                  size="sm"
                  variant="danger"
                  onClick={handleDisable2FA}
                  disabled={!disableVerificationCode || isDisabling}
                >
                  {isDisabling ? <LoadingSpinner size="xs" /> : 'Disable 2FA'}
                </Button>
              </div>
            </div>
          </div>
        ) : (
          // Setup Options
          <div className="space-y-4">
            {!setupMode ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Authenticator App */}
                <div className="bg-gray-700 rounded-lg p-4 cursor-pointer hover:bg-gray-600 transition-colors">
                  <div className="flex flex-col items-center text-center space-y-3">
                    <div className="text-purple-400">
                      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 1.182C4.77 15.916 3 13.658 3 11c0-4.418 4.03-8 9-8s9 3.582 9 8c0 2.658-1.77 4.916-3 7.182" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-white font-medium">Authenticator App</h4>
                      <p className="text-gray-400 text-xs mt-1">
                        Google Authenticator, Authy, or similar
                      </p>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleStartSetup('totp')}
                      disabled={isEnabling}
                    >
                      Setup
                    </Button>
                  </div>
                </div>

                {/* SMS */}
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex flex-col items-center text-center space-y-3">
                    <div className="text-blue-400">
                      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M8 21h8a1 1 0 001-1V4a1 1 0 00-1-1H8a1 1 0 00-1 1v16a1 1 0 001 1z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-white font-medium">SMS</h4>
                      <p className="text-gray-400 text-xs mt-1">
                        Receive codes via text message
                      </p>
                    </div>
                    <input
                      type="tel"
                      placeholder="Phone number"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-purple-500"
                    />
                    <Button
                      size="sm"
                      onClick={() => handleStartSetup('sms')}
                      disabled={isEnabling || !phoneNumber}
                    >
                      Setup
                    </Button>
                  </div>
                </div>

                {/* Email */}
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex flex-col items-center text-center space-y-3">
                    <div className="text-green-400">
                      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-white font-medium">Email</h4>
                      <p className="text-gray-400 text-xs mt-1">
                        Receive codes via email
                      </p>
                    </div>
                    <input
                      type="email"
                      placeholder="Email address"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-purple-500"
                    />
                    <Button
                      size="sm"
                      onClick={() => handleStartSetup('email')}
                      disabled={isEnabling || !email}
                    >
                      Setup
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              // Setup Process
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-white font-medium">
                    Setting up {setupMode === 'totp' ? 'Authenticator App' : setupMode.toUpperCase()}
                  </h4>
                  <Button size="sm" variant="outline" onClick={resetSetup}>
                    Cancel
                  </Button>
                </div>

                <div className="space-y-4">
                  {setupMode === 'totp' && (
                    <>
                      <SetupStep
                        step={1}
                        title="Install an authenticator app"
                        isActive={setupStep === 1}
                        isCompleted={setupStep > 1}
                      >
                        <p className="text-gray-400 text-sm">
                          Download Google Authenticator, Authy, or another TOTP app.
                        </p>
                      </SetupStep>

                      <SetupStep
                        step={2}
                        title="Scan the QR code"
                        isActive={setupStep === 2}
                        isCompleted={setupStep > 2}
                      >
                        {qrCode && (
                          <div className="space-y-3">
                            <div className="bg-white p-4 rounded-lg inline-block">
                              <img src={qrCode} alt="2FA QR Code" className="w-48 h-48" />
                            </div>
                            <p className="text-gray-400 text-sm">
                              Scan this QR code with your authenticator app.
                            </p>
                          </div>
                        )}
                      </SetupStep>
                    </>
                  )}

                  <SetupStep
                    step={setupMode === 'totp' ? 3 : 2}
                    title="Enter verification code"
                    isActive={setupStep === (setupMode === 'totp' ? 2 : 2)}
                    isCompleted={setupStep > (setupMode === 'totp' ? 2 : 2)}
                  >
                    <div className="space-y-3">
                      <input
                        type="text"
                        placeholder="Enter 6-digit code"
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                        maxLength={6}
                      />
                      <Button
                        onClick={handleVerifySetup}
                        disabled={verificationCode.length !== 6 || isVerifying}
                      >
                        {isVerifying ? <LoadingSpinner size="xs" /> : 'Verify'}
                      </Button>
                    </div>
                  </SetupStep>

                  {setupStep === 3 && (
                    <SetupStep
                      step={setupMode === 'totp' ? 4 : 3}
                      title="Save backup codes"
                      isActive={true}
                      isCompleted={false}
                    >
                      <div className="space-y-3">
                        <p className="text-gray-400 text-sm">
                          Save these backup codes in a secure location. You can use them to access your account if you lose your phone.
                        </p>
                        <div className="bg-gray-700 rounded p-4">
                          <div className="grid grid-cols-2 gap-2 text-sm font-mono">
                            {backupCodes.map((code, index) => (
                              <div key={index} className="text-white">{code}</div>
                            ))}
                          </div>
                        </div>
                        <div className="flex space-x-3">
                          <Button size="sm" onClick={downloadBackupCodes}>
                            Download Codes
                          </Button>
                          <Button size="sm" variant="outline" onClick={resetSetup}>
                            Done
                          </Button>
                        </div>
                      </div>
                    </SetupStep>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Backup Codes Display */}
      {showBackupCodes && (
        <div className="bg-yellow-900 bg-opacity-20 border border-yellow-700 rounded-lg p-4">
          <h4 className="text-yellow-300 font-medium mb-3">Your New Backup Codes</h4>
          <div className="bg-gray-800 rounded p-4 mb-3">
            <div className="grid grid-cols-2 gap-2 text-sm font-mono">
              {backupCodes.map((code, index) => (
                <div key={index} className="text-white">{code}</div>
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Button size="sm" onClick={downloadBackupCodes}>
              Download
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowBackupCodes(false)}>
              I've saved them
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TwoFactorAuth;