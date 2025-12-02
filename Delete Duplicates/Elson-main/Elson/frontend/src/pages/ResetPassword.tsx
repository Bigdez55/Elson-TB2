import React from 'react';
import ResetPasswordComponent from '../app/components/auth/ResetPassword';

export default function ResetPassword() {
  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="text-center text-3xl font-bold text-white">
          Elson Wealth
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <ResetPasswordComponent />
      </div>
    </div>
  );
}