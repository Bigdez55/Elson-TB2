import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '../../services/auth';
import Button from '../common/Button';
import Card from '../common/Card';
import Input from '../common/Input';
import LoadingSpinner from '../common/LoadingSpinner';

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('Please enter your email address');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await authService.requestPasswordReset(email);
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to process your request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="max-w-md mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6 text-center">Reset Your Password</h2>
      
      {success ? (
        <div className="text-center">
          <div className="bg-green-900/30 text-green-300 p-4 rounded-lg mb-4">
            <p>Password reset instructions have been sent to your email.</p>
            <p className="text-sm mt-2">Please check your inbox and follow the instructions.</p>
          </div>
          
          <Link to="/login" className="text-purple-400 hover:text-purple-300 inline-block mt-4">
            Return to Login
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-gray-300 mb-4">
            Enter the email address associated with your account, and we'll send you instructions to reset your password.
          </p>
          
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            aria-label="Email address"
            autoFocus
          />
          
          {error && (
            <div className="text-red-500 text-sm">{error}</div>
          )}
          
          <Button
            type="submit"
            disabled={loading || !email}
            className="w-full"
            variant="primary"
          >
            {loading ? <LoadingSpinner size="small" /> : 'Send Reset Instructions'}
          </Button>
          
          <div className="text-center mt-4">
            <Link to="/login" className="text-gray-400 hover:text-white text-sm">
              Back to Login
            </Link>
          </div>
        </form>
      )}
    </Card>
  );
};

export default ForgotPassword;