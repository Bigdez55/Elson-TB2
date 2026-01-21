import React, { useState } from 'react';
import { startRegistration } from '@simplewebauthn/browser';

interface BiometricSetupProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

interface WebAuthnCredential {
  id: number;
  credential_id: string;
  credential_name: string;
  device_type: string;
  authenticator_type: string;
  is_active: boolean;
  last_used: string | null;
  created_at: string;
}

export const BiometricSetup: React.FC<BiometricSetupProps> = ({
  onSuccess,
  onCancel,
}) => {
  const [credentialName, setCredentialName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'name' | 'register'>('name');

  const handleStartSetup = async () => {
    if (!credentialName.trim()) {
      setError('Please enter a name for this device');
      return;
    }

    setLoading(true);
    setError(null);
    setStep('register');

    try {
      // Check WebAuthn support
      if (!window.PublicKeyCredential) {
        throw new Error(
          'Your browser does not support biometric authentication. Please use a modern browser like Chrome, Safari, or Edge.'
        );
      }

      // Step 1: Start registration
      const token = localStorage.getItem('access_token');
      const startResponse = await fetch(
        '/api/v1/biometric/register/start',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ credential_name: credentialName }),
        }
      );

      if (!startResponse.ok) {
        const errorData = await startResponse.json();
        throw new Error(errorData.detail || 'Failed to start registration');
      }

      const options = await startResponse.json();

      // Step 2: Call browser WebAuthn API
      // Convert server response to WebAuthn options format
      const webAuthnOptions = {
        challenge: options.challenge,
        rp: {
          name: options.rp_name,
          id: options.rp_id,
        },
        user: {
          id: options.user_id,
          name: options.user_name,
          displayName: options.user_display_name,
        },
        pubKeyCredParams: options.pub_key_cred_params,
        timeout: options.timeout,
        attestation: options.attestation,
        authenticatorSelection: options.authenticator_selection,
      };
      const attestationResponse = await startRegistration({ optionsJSON: webAuthnOptions as any });

      // Step 3: Complete registration
      const completeResponse = await fetch(
        '/api/v1/biometric/register/complete',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            credential_id: attestationResponse.id,
            client_data_json: attestationResponse.response.clientDataJSON,
            attestation_object:
              attestationResponse.response.attestationObject,
            credential_name: credentialName,
            authenticator_type: attestationResponse.authenticatorAttachment,
          }),
        }
      );

      if (!completeResponse.ok) {
        const errorData = await completeResponse.json();
        throw new Error(errorData.detail || 'Failed to complete registration');
      }

      const result = await completeResponse.json();

      // Success
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      console.error('Biometric setup error:', err);
      setError(
        err.message ||
          'Failed to set up biometric authentication. Please try again.'
      );
      setStep('name');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="biometric-setup">
      <div className="biometric-setup-header">
        <h3>Set Up Biometric Authentication</h3>
        <p className="text-muted">
          Use your fingerprint, face, or security key to sign in quickly and
          securely
        </p>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {step === 'name' && (
        <div className="form-group">
          <label htmlFor="credential-name">
            Device Name
            <span className="text-muted ml-2">
              (e.g., "MacBook Touch ID", "iPhone Face ID")
            </span>
          </label>
          <input
            type="text"
            id="credential-name"
            className="form-control"
            placeholder="My Device"
            value={credentialName}
            onChange={(e) => setCredentialName(e.target.value)}
            disabled={loading}
            maxLength={255}
          />
          <small className="form-text text-muted">
            This helps you identify which device you're using
          </small>
        </div>
      )}

      {step === 'register' && loading && (
        <div className="text-center py-4">
          <div className="spinner-border text-primary" role="status">
            <span className="sr-only">Loading...</span>
          </div>
          <p className="mt-3">
            Follow the prompts on your device to complete setup...
          </p>
          <p className="text-muted">
            You may be asked to use your fingerprint, face, or security key
          </p>
        </div>
      )}

      <div className="biometric-setup-actions mt-4">
        {step === 'name' && (
          <>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleStartSetup}
              disabled={loading || !credentialName.trim()}
            >
              {loading ? 'Setting up...' : 'Set Up Biometric'}
            </button>
            {onCancel && (
              <button
                type="button"
                className="btn btn-secondary ml-2"
                onClick={onCancel}
                disabled={loading}
              >
                Cancel
              </button>
            )}
          </>
        )}
      </div>

      <div className="biometric-info mt-4 p-3 bg-light rounded">
        <h5 className="text-sm font-weight-bold">Supported Methods:</h5>
        <ul className="mb-0">
          <li>Touch ID (Mac, iPhone, iPad)</li>
          <li>Face ID (iPhone, iPad)</li>
          <li>Windows Hello (fingerprint or face)</li>
          <li>Android fingerprint</li>
          <li>Hardware security keys (YubiKey, etc.)</li>
        </ul>
      </div>
    </div>
  );
};

export default BiometricSetup;
