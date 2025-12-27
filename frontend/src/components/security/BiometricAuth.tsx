import React, { useState } from 'react';
import { startAuthentication } from '@simplewebauthn/browser';
import { useNavigate } from 'react-router-dom';

interface BiometricAuthProps {
  username?: string;
  onSuccess?: (tokens: { access_token: string; refresh_token: string }) => void;
  onError?: (error: string) => void;
}

export const BiometricAuth: React.FC<BiometricAuthProps> = ({
  username,
  onSuccess,
  onError,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleBiometricLogin = async () => {
    setLoading(true);
    setError(null);

    try {
      // Check WebAuthn support
      if (!window.PublicKeyCredential) {
        throw new Error(
          'Your browser does not support biometric authentication'
        );
      }

      // Step 1: Start authentication
      const startResponse = await fetch(
        '/api/v1/biometric/authenticate/start',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username: username || null }),
        }
      );

      if (!startResponse.ok) {
        const errorData = await startResponse.json();
        throw new Error(
          errorData.detail || 'Failed to start biometric authentication'
        );
      }

      const options = await startResponse.json();

      // Step 2: Call browser WebAuthn API
      const assertionResponse = await startAuthentication({
        challenge: options.challenge,
        rpId: options.rp_id,
        timeout: options.timeout,
        userVerification: options.user_verification,
        allowCredentials: options.allowed_credentials.map((cred: any) => ({
          type: cred.type,
          id: cred.id,
        })),
      });

      // Step 3: Complete authentication
      const completeResponse = await fetch(
        '/api/v1/biometric/authenticate/complete',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            credential_id: assertionResponse.id,
            client_data_json: assertionResponse.response.clientDataJSON,
            authenticator_data: assertionResponse.response.authenticatorData,
            signature: assertionResponse.response.signature,
            user_handle: assertionResponse.response.userHandle,
          }),
        }
      );

      if (!completeResponse.ok) {
        const errorData = await completeResponse.json();
        throw new Error(
          errorData.detail || 'Biometric authentication failed'
        );
      }

      const result = await completeResponse.json();

      // Store tokens
      localStorage.setItem('access_token', result.access_token);
      localStorage.setItem('refresh_token', result.refresh_token);

      // Call success callback
      if (onSuccess) {
        onSuccess({
          access_token: result.access_token,
          refresh_token: result.refresh_token,
        });
      } else {
        // Default: navigate to dashboard
        navigate('/dashboard');
      }
    } catch (err: any) {
      console.error('Biometric authentication error:', err);
      const errorMessage =
        err.message || 'Biometric authentication failed. Please try again.';
      setError(errorMessage);
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="biometric-auth">
      {error && (
        <div className="alert alert-danger mb-3" role="alert">
          {error}
        </div>
      )}

      <button
        type="button"
        className="btn btn-outline-primary btn-block biometric-login-btn"
        onClick={handleBiometricLogin}
        disabled={loading}
      >
        {loading ? (
          <>
            <span
              className="spinner-border spinner-border-sm mr-2"
              role="status"
              aria-hidden="true"
            ></span>
            Authenticating...
          </>
        ) : (
          <>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              fill="currentColor"
              className="bi bi-fingerprint mr-2"
              viewBox="0 0 16 16"
              style={{ display: 'inline-block', verticalAlign: 'middle' }}
            >
              <path d="M8.06 6.5a.5.5 0 0 1 .5.5v.776a11.5 11.5 0 0 1-.552 3.519l-1.331 4.14a.5.5 0 0 1-.952-.305l1.33-4.141a10.5 10.5 0 0 0 .505-3.213V7a.5.5 0 0 1 .5-.5Z" />
              <path d="M6.06 7a2 2 0 1 1 4 0 .5.5 0 1 1-1 0 1 1 0 1 0-2 0v.332q0 .613-.066 1.221A.5.5 0 0 1 6 8.447q.06-.555.06-1.115zm3.509 1a.5.5 0 0 1 .487.513 11.5 11.5 0 0 1-.587 3.339l-1.266 3.8a.5.5 0 0 1-.949-.317l1.267-3.8a10.5 10.5 0 0 0 .535-3.048A.5.5 0 0 1 9.569 8m-3.356 2.115a.5.5 0 0 1 .33.626L5.24 14.939a.5.5 0 1 1-.955-.296l1.303-4.199a.5.5 0 0 1 .625-.329" />
              <path d="M4.759 5.833A3.501 3.501 0 0 1 11.559 7a.5.5 0 0 1-1 0 2.5 2.5 0 0 0-4.857-.833.5.5 0 1 1-.943-.334m.3 1.67a.5.5 0 0 1 .449.546 10.7 10.7 0 0 1-.4 2.031l-1.222 4.072a.5.5 0 1 1-.958-.287L4.15 9.793a9.7 9.7 0 0 0 .363-1.842.5.5 0 0 1 .546-.449Zm6 .647a.5.5 0 0 1 .5.5c0 1.28-.213 2.552-.632 3.762l-1.09 3.145a.5.5 0 0 1-.944-.327l1.089-3.145c.382-1.105.578-2.266.578-3.435a.5.5 0 0 1 .5-.5Z" />
              <path d="M3.902 4.222a5 5 0 0 1 8.196 0 .5.5 0 0 1-.793.627 4 4 0 0 0-6.61 0 .5.5 0 0 1-.793-.627m-.964 1.449a.5.5 0 0 1 .445.551 12.5 12.5 0 0 1-.508 2.595l-1.076 3.825a.5.5 0 1 1-.964-.271l1.076-3.826c.18-.638.337-1.293.437-1.968a.5.5 0 0 1 .59-.406" />
            </svg>
            Sign in with Biometric
          </>
        )}
      </button>

      <div className="text-center mt-3 text-muted">
        <small>
          Use Touch ID, Face ID, Windows Hello, or your security key
        </small>
      </div>
    </div>
  );
};

export default BiometricAuth;
