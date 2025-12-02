import React from 'react';
import { useSelector } from 'react-redux';
import { Navigate, useLocation } from 'react-router-dom';
import TwoFactorVerification from '../app/components/auth/TwoFactorVerification';
import { RootState } from '../app/store/store';

export default function TwoFactorAuth() {
  const { requires2FA, twoFactorEmail } = useSelector((state: RootState) => state.user);
  const location = useLocation();
  
  // If 2FA is not required, redirect to login
  if (!requires2FA || !twoFactorEmail) {
    return <Navigate to="/login" replace />;
  }
  
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="text-center text-3xl font-bold text-white">
          Elson Wealth
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <TwoFactorVerification email={twoFactorEmail} />
      </div>
    </div>
  );
}