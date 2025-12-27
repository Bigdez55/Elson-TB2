import React, { useState, useEffect } from 'react';
import BiometricSetup from './BiometricSetup';
import { LoadingSpinner } from '../common/LoadingSpinner';

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

export const BiometricManagement: React.FC = () => {
  const [credentials, setCredentials] = useState<WebAuthnCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSetup, setShowSetup] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCredentials = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/biometric/credentials', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load biometric credentials');
      }

      const data = await response.json();
      setCredentials(data.credentials || []);
    } catch (err: any) {
      console.error('Error loading credentials:', err);
      setError(err.message || 'Failed to load biometric credentials');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCredentials();
  }, []);

  const handleDeleteCredential = async (credentialId: number) => {
    if (
      !confirm(
        'Are you sure you want to remove this biometric credential? You can always add it again later.'
      )
    ) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `/api/v1/biometric/credentials/${credentialId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete credential');
      }

      // Reload credentials
      await loadCredentials();
    } catch (err: any) {
      alert(err.message || 'Failed to delete credential');
    }
  };

  const handleSetupSuccess = () => {
    setShowSetup(false);
    loadCredentials();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getDeviceIcon = (authenticatorType: string) => {
    if (authenticatorType === 'platform') {
      return (
        <svg
          className="h-6 w-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>
      );
    }
    return (
      <svg
        className="h-6 w-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
        />
      </svg>
    );
  };

  if (showSetup) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <BiometricSetup
          onSuccess={handleSetupSuccess}
          onCancel={() => setShowSetup(false)}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-white">
            Biometric Authentication
          </h3>
          <p className="text-gray-400 text-sm mt-1">
            Manage your fingerprint, face, and security key credentials
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowSetup(true)}
          disabled={loading}
        >
          <svg
            className="h-4 w-4 mr-2 inline-block"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Biometric
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="sm" />
          <span className="ml-2 text-gray-400">Loading credentials...</span>
        </div>
      ) : credentials.length === 0 ? (
        /* Empty State */
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <div className="text-purple-400 mb-4">
            <svg
              className="h-16 w-16 mx-auto"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"
              />
            </svg>
          </div>
          <h4 className="text-white font-medium text-lg mb-2">
            No Biometric Credentials
          </h4>
          <p className="text-gray-400 mb-4">
            Set up fingerprint, Face ID, or a security key for quick and secure
            sign-in
          </p>
          <button
            className="btn btn-primary"
            onClick={() => setShowSetup(true)}
          >
            Set Up Biometric Authentication
          </button>
        </div>
      ) : (
        /* Credentials List */
        <div className="bg-gray-800 rounded-lg divide-y divide-gray-700">
          {credentials.map((credential) => (
            <div
              key={credential.id}
              className="p-6 flex items-start justify-between hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-start space-x-4">
                <div className="text-purple-400 mt-1">
                  {getDeviceIcon(credential.authenticator_type)}
                </div>
                <div className="flex-1">
                  <h4 className="text-white font-medium">
                    {credential.credential_name || 'Unnamed Device'}
                  </h4>
                  <div className="mt-1 space-y-1">
                    <p className="text-gray-400 text-sm">
                      {credential.device_type || 'Biometric Device'}
                      {credential.authenticator_type === 'platform' && (
                        <span className="ml-2 text-xs bg-purple-900 text-purple-300 px-2 py-0.5 rounded">
                          Built-in
                        </span>
                      )}
                      {credential.authenticator_type === 'cross-platform' && (
                        <span className="ml-2 text-xs bg-blue-900 text-blue-300 px-2 py-0.5 rounded">
                          Security Key
                        </span>
                      )}
                    </p>
                    <p className="text-gray-500 text-xs">
                      Added {formatDate(credential.created_at)}
                    </p>
                    {credential.last_used && (
                      <p className="text-gray-500 text-xs">
                        Last used {formatDate(credential.last_used)}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {credential.is_active ? (
                  <span className="text-green-400 text-xs bg-green-900 px-2 py-1 rounded">
                    Active
                  </span>
                ) : (
                  <span className="text-gray-400 text-xs bg-gray-700 px-2 py-1 rounded">
                    Inactive
                  </span>
                )}
                <button
                  className="btn btn-sm btn-outline-danger"
                  onClick={() => handleDeleteCredential(credential.id)}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info */}
      <div className="bg-blue-900 bg-opacity-20 border border-blue-700 rounded-lg p-4">
        <h4 className="text-blue-300 font-medium mb-2 flex items-center">
          <svg
            className="h-5 w-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          How it works
        </h4>
        <ul className="text-blue-200 text-sm space-y-1 ml-7">
          <li>
            Your biometric data (fingerprint, face) never leaves your device
          </li>
          <li>Only a cryptographic key is stored on our servers</li>
          <li>You can register multiple devices for convenience</li>
          <li>Remove credentials anytime from this page</li>
        </ul>
      </div>
    </div>
  );
};

export default BiometricManagement;
