import React from 'react';
import ForgotPasswordComponent from '../app/components/auth/ForgotPassword';

export default function ForgotPassword() {
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="text-center text-3xl font-bold text-white">
          Elson Wealth
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <ForgotPasswordComponent />
      </div>
    </div>
  );
}