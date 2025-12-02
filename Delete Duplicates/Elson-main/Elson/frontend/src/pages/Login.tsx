import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/common/Button';
import Input from '../components/common/Input';

export default function LoginPage() {
  const { login, loading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, password);
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="text-center text-3xl font-bold text-white">
          Trading Bot Login
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-gray-800 py-8 px-6 shadow rounded-lg">
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />

            {error && (
              <div className="text-red-500 text-sm">{error}</div>
            )}

            <div className="flex items-center justify-between">
              <div className="text-sm">
                <Link
                  to="/forgot-password"
                  className="text-primary-500 hover:text-primary-400"
                >
                  Forgot your password?
                </Link>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              fullWidth
              isLoading={loading}
            >
              Sign in
            </Button>

            <div className="text-center">
              <span className="text-gray-400">Don't have an account?</span>{' '}
              <Link
                to="/register"
                className="text-primary-500 hover:text-primary-400"
              >
                Register here
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}