import React from 'react';
import Input from '../../common/Input';

interface AccountDetailsStepProps {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  phone: string;
  agreeToTerms: boolean;
  setFirstName: (value: string) => void;
  setLastName: (value: string) => void;
  setEmail: (value: string) => void;
  setPassword: (value: string) => void;
  setConfirmPassword: (value: string) => void;
  setPhone: (value: string) => void;
  setAgreeToTerms: (value: boolean) => void;
  validationError: string | null;
  validateStep: () => boolean;
}

const AccountDetailsStep: React.FC<AccountDetailsStepProps> = ({
  firstName,
  lastName,
  email,
  password,
  confirmPassword,
  phone,
  agreeToTerms,
  setFirstName,
  setLastName,
  setEmail,
  setPassword,
  setConfirmPassword,
  setPhone,
  setAgreeToTerms,
  validationError,
}) => {
  // Password strength checks
  const hasMinLength = password.length >= 8;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password);
  const passwordsMatch = password === confirmPassword;
  
  const passwordStrength = 
    (hasMinLength ? 1 : 0) + 
    (hasUpperCase ? 1 : 0) + 
    (hasLowerCase ? 1 : 0) + 
    (hasNumber ? 1 : 0) + 
    (hasSpecialChar ? 1 : 0);
  
  const getPasswordStrengthColor = () => {
    if (passwordStrength < 2) return 'bg-red-500';
    if (passwordStrength < 4) return 'bg-yellow-500';
    return 'bg-green-500';
  };
  
  const getPasswordStrengthText = () => {
    if (passwordStrength < 2) return 'Weak';
    if (passwordStrength < 4) return 'Medium';
    return 'Strong';
  };

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">Create your Elson account</h2>
        <p className="text-gray-400">Let&apos;s start by setting up your login details</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Input
          label="First Name"
          type="text"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          placeholder="Enter your first name"
          required
        />
        <Input
          label="Last Name"
          type="text"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          placeholder="Enter your last name"
          required
        />
      </div>

      <Input
        label="Email Address"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@example.com"
        required
      />

      <div className="space-y-1">
        <Input
          label="Create Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Create a secure password"
          required
        />
        
        {password && (
          <div className="mt-2">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-gray-400">Password strength:</span>
              <span className="text-sm font-medium" 
                style={{ color: getPasswordStrengthColor() === 'bg-red-500' ? '#f87171' : 
                  getPasswordStrengthColor() === 'bg-yellow-500' ? '#fcd34d' : '#4ade80' }}>
                {getPasswordStrengthText()}
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className={`${getPasswordStrengthColor()} h-2 rounded-full transition-all`}
                style={{ width: `${(passwordStrength / 5) * 100}%` }}
              ></div>
            </div>
            
            <div className="grid grid-cols-2 gap-2 mt-3">
              <div className="text-xs text-gray-400 flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${hasMinLength ? 'bg-green-500' : 'bg-gray-600'}`}></div>
                <span>8+ characters</span>
              </div>
              <div className="text-xs text-gray-400 flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${hasUpperCase ? 'bg-green-500' : 'bg-gray-600'}`}></div>
                <span>Uppercase letter</span>
              </div>
              <div className="text-xs text-gray-400 flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${hasLowerCase ? 'bg-green-500' : 'bg-gray-600'}`}></div>
                <span>Lowercase letter</span>
              </div>
              <div className="text-xs text-gray-400 flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${hasNumber ? 'bg-green-500' : 'bg-gray-600'}`}></div>
                <span>Number</span>
              </div>
              <div className="text-xs text-gray-400 flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${hasSpecialChar ? 'bg-green-500' : 'bg-gray-600'}`}></div>
                <span>Special character</span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <Input
        label="Confirm Password"
        type="password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        placeholder="Confirm your password"
        required
        error={confirmPassword && !passwordsMatch ? "Passwords don't match" : undefined}
      />

      <Input
        label="Phone Number (for 2FA)"
        type="tel"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        placeholder="(123) 456-7890"
        required
      />

      <div className="mt-4">
        <label className="flex items-center">
          <input 
            type="checkbox" 
            className="h-4 w-4 text-purple-600 rounded border-gray-700 focus:ring-purple-500"
            checked={agreeToTerms}
            onChange={(e) => setAgreeToTerms(e.target.checked)}
          />
          <span className="ml-2 text-sm text-gray-400">
            I agree to Elson&apos;s <a href="#" className="text-purple-400 hover:text-purple-300">Terms of Service</a> and <a href="#" className="text-purple-400 hover:text-purple-300">Privacy Policy</a>
          </span>
        </label>
      </div>

      {validationError && (
        <div className="text-red-500 text-sm">
          {validationError}
        </div>
      )}
    </div>
  );
};

export default AccountDetailsStep;