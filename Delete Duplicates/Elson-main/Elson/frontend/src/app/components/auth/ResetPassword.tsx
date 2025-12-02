import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { authService } from '../../services/auth';
import Button from '../common/Button';
import Card from '../common/Card';
import Input from '../common/Input';
import LoadingSpinner from '../common/LoadingSpinner';

// Password strength indicator component
const PasswordStrengthIndicator: React.FC<{ password: string }> = ({ password }) => {
  const getStrength = (password: string): { strength: number; label: string; color: string } => {
    if (!password) return { strength: 0, label: 'None', color: 'bg-gray-600' };
    
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    
    // Character type checks
    if (/[a-z]/.test(password)) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
    
    // Map strength score to label and color
    const strengthMap = [
      { threshold: 0, label: 'None', color: 'bg-gray-600' },
      { threshold: 2, label: 'Weak', color: 'bg-red-600' },
      { threshold: 4, label: 'Medium', color: 'bg-yellow-600' },
      { threshold: 6, label: 'Strong', color: 'bg-green-600' }
    ];
    
    const strengthLevel = strengthMap.findIndex(level => strength <= level.threshold);
    const result = strengthMap[strengthLevel === -1 ? strengthMap.length - 1 : strengthLevel];
    
    return { 
      strength: strength, 
      label: result.label, 
      color: result.color 
    };
  };
  
  const { strength, label, color } = getStrength(password);
  const percentage = Math.min((strength / 6) * 100, 100);
  
  return (
    <div className="my-2">
      <div className="flex justify-between text-xs mb-1">
        <span>Password Strength</span>
        <span>{label}</span>
      </div>
      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${color} transition-all duration-300`} 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const ResetPassword: React.FC = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract token from URL query parameters
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const tokenParam = queryParams.get('token');
    
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      setError('Missing reset token. Please use the link from your email.');
    }
  }, [location.search]);
  
  const validatePassword = (password: string): boolean => {
    // Minimum length of 8 characters
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    
    // Require at least one lowercase letter, one uppercase letter, one number, and one special character
    const hasLowercase = /[a-z]/.test(password);
    const hasUppercase = /[A-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecialChar = /[^a-zA-Z0-9]/.test(password);
    
    if (!hasLowercase || !hasUppercase || !hasNumber || !hasSpecialChar) {
      setError('Password must include at least one lowercase letter, one uppercase letter, one number, and one special character');
      return false;
    }
    
    return true;
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate passwords
    if (!password || !confirmPassword) {
      setError('Please enter and confirm your password');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (!validatePassword(password)) {
      return;
    }
    
    if (!token) {
      setError('Missing reset token. Please use the link from your email.');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await authService.resetPassword(token, password);
      setSuccess(true);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login', { 
          state: { 
            message: 'Your password has been reset successfully. Please log in with your new password.' 
          } 
        });
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to reset password. The link may have expired.');
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
            <p>Your password has been reset successfully!</p>
            <p className="text-sm mt-2">Redirecting to login page...</p>
          </div>
          
          <Link to="/login" className="text-purple-400 hover:text-purple-300 inline-block mt-4">
            Go to Login
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {!token && (
            <div className="bg-red-900/30 text-red-300 p-4 rounded-lg mb-4">
              <p>Invalid or missing reset token.</p>
              <p className="text-sm mt-2">Please use the link from your email or request a new password reset.</p>
            </div>
          )}
          
          <div>
            <Input
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError(null);
              }}
              placeholder="New password"
              aria-label="New password"
              disabled={!token || loading}
              autoFocus
            />
            <PasswordStrengthIndicator password={password} />
          </div>
          
          <Input
            type="password"
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setError(null);
            }}
            placeholder="Confirm new password"
            aria-label="Confirm new password"
            disabled={!token || loading}
          />
          
          {error && (
            <div className="text-red-500 text-sm">{error}</div>
          )}
          
          <Button
            type="submit"
            disabled={!token || loading || !password || !confirmPassword}
            className="w-full"
            variant="primary"
          >
            {loading ? <LoadingSpinner size="small" /> : 'Reset Password'}
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

export default ResetPassword;