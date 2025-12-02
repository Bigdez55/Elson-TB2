import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { verify2FA } from '../../store/slices/userSlice';
import { authService } from '../../services/auth';
import Button from '../common/Button';
import Card from '../common/Card';
import Input from '../common/Input';
import LoadingSpinner from '../common/LoadingSpinner';

interface TwoFactorVerificationProps {
  email?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const TwoFactorVerification: React.FC<TwoFactorVerificationProps> = ({ 
  email: propEmail, 
  onSuccess, 
  onCancel 
}) => {
  const [code, setCode] = useState<string>('');
  const [email, setEmail] = useState<string>(propEmail || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState<number>(30);
  const [canResend, setCanResend] = useState<boolean>(false);
  
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract email from state if not provided via props
  useEffect(() => {
    if (!propEmail && location.state?.email) {
      setEmail(location.state.email);
    }
  }, [propEmail, location.state]);
  
  // Timer for code resend
  useEffect(() => {
    if (remainingSeconds <= 0) {
      setCanResend(true);
      return;
    }
    
    const timer = setTimeout(() => {
      setRemainingSeconds(prev => prev - 1);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [remainingSeconds]);
  
  // Handle code input
  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;
    // Only allow numbers and limit to 6 digits
    if (/^\d*$/.test(input) && input.length <= 6) {
      setCode(input);
      setError(null);
    }
  };
  
  // Handle verification
  const handleVerify = async () => {
    if (!code || code.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await authService.verify2FA(email, code);
      
      // Dispatch action to update user state with the token
      dispatch(verify2FA(response));
      
      // Invoke success callback or redirect
      if (onSuccess) {
        onSuccess();
      } else {
        // Get the redirect path from location state or default to dashboard
        const from = location.state?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Invalid verification code. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle resend code
  const handleResendCode = async () => {
    if (!canResend) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await authService.request2FACode(email);
      setRemainingSeconds(30);
      setCanResend(false);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to resend code. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle cancel
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      navigate('/login');
    }
  };
  
  return (
    <Card className="max-w-md mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6 text-center">Two-Factor Verification</h2>
      <p className="text-gray-300 mb-6 text-center">
        A verification code has been sent to your email address. 
        Please enter the 6-digit code below.
      </p>
      
      <div className="space-y-4">
        <Input
          type="text"
          value={code}
          onChange={handleCodeChange}
          placeholder="Enter 6-digit code"
          aria-label="Verification code"
          className="text-center tracking-widest text-2xl"
          autoFocus
        />
        
        {error && (
          <div className="text-red-500 text-sm text-center">{error}</div>
        )}
        
        <Button
          onClick={handleVerify}
          disabled={loading || code.length !== 6}
          className="w-full"
          variant="primary"
        >
          {loading ? <LoadingSpinner size="small" /> : 'Verify'}
        </Button>
        
        <div className="flex justify-between items-center mt-4">
          <button
            type="button"
            onClick={handleCancel}
            className="text-gray-400 hover:text-white text-sm"
          >
            Cancel
          </button>
          
          <button
            type="button"
            onClick={handleResendCode}
            disabled={!canResend || loading}
            className={`text-sm ${canResend ? 'text-purple-400 hover:text-purple-300' : 'text-gray-500'}`}
          >
            {canResend ? 'Resend code' : `Resend in ${remainingSeconds}s`}
          </button>
        </div>
      </div>
    </Card>
  );
};

export default TwoFactorVerification;