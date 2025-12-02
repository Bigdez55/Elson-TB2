import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../app/hooks/useAuth';
import Button from '../app/components/common/Button';
import Input from '../app/components/common/Input';
import Select from '../app/components/common/Select';
import { isValidPassword } from '../app/utils/validators';

// Step types to track onboarding process
type Step = 'account' | 'bank' | 'profile' | 'identity';

// Risk option type for investment profile
type RiskOption = {
  id: string;
  title: string;
  description?: string;
};

export default function RegisterPage() {
  const { register, loading, error } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<Step>('account');
  const [validationError, setValidationError] = useState<string | null>(null);

  // Step 1: Account Details
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [agreeToTerms, setAgreeToTerms] = useState(false);

  // Step 2: Bank Connection
  const [bankName, setBankName] = useState('');
  const [routingNumber, setRoutingNumber] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [accountType, setAccountType] = useState('');

  // Step 3: Investment Profile
  const [accountType, setAccountTypeValue] = useState<string>('');
  const [investmentGoal, setInvestmentGoal] = useState<string>('');
  const [riskTolerance, setRiskTolerance] = useState<string>('');
  const [aiManaged, setAiManaged] = useState<string>('');

  // Step 4: Identity Verification
  const [ssn, setSsn] = useState('');
  const [dob, setDob] = useState('');
  const [streetAddress, setStreetAddress] = useState('');
  const [aptSuite, setAptSuite] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [idType, setIdType] = useState('');
  const [certifyInfo, setCertifyInfo] = useState(false);

  // Bank options 
  const bankOptions = [
    { name: 'Chase', logo: '🏦' },
    { name: 'Bank of America', logo: '🏦' },
    { name: 'Wells Fargo', logo: '🏦' },
    { name: 'Citibank', logo: '🏦' },
    { name: 'Capital One', logo: '🏦' },
    { name: 'Other Bank', logo: '➕' }
  ];

  // Account type options
  const accountTypeOptions: RiskOption[] = [
    {
      id: 'personal',
      title: 'Personal Account',
      description: 'Invest for yourself with a standard brokerage account'
    },
    {
      id: 'custodial',
      title: 'Custodial Account',
      description: 'Invest on behalf of a minor (under 18)'
    }
  ];

  // Investment goal options
  const investmentGoalOptions: RiskOption[] = [
    { id: 'retirement', title: 'Saving for retirement' },
    { id: 'wealth', title: 'Building long-term wealth' },
    { id: 'major-purchase', title: 'Saving for a major purchase (home, education, etc.)' },
    { id: 'income', title: 'Generating income' },
    { id: 'trading', title: 'Short-term trading profits' }
  ];

  // Risk tolerance options
  const riskToleranceOptions: RiskOption[] = [
    {
      id: 'conservative',
      title: 'Conservative',
      description: 'I want to minimize risk and am willing to accept lower returns'
    },
    {
      id: 'moderate',
      title: 'Moderate',
      description: 'I\'m comfortable with some fluctuations to achieve better returns'
    },
    {
      id: 'aggressive',
      title: 'Aggressive',
      description: 'I\'m willing to accept significant volatility for potentially higher returns'
    }
  ];

  // AI Management options
  const aiManagementOptions: RiskOption[] = [
    {
      id: 'ai-managed',
      title: 'Yes, AI-managed',
      description: 'Let our quantum AI build and manage a personalized portfolio for you'
    },
    {
      id: 'self-directed',
      title: 'No, self-directed',
      description: 'I prefer to make my own investment decisions (you can change this later)'
    }
  ];

  // ID type options for the dropdown
  const idTypeOptions = [
    { value: 'drivers-license', label: 'Driver\'s License' },
    { value: 'passport', label: 'Passport' },
    { value: 'state-id', label: 'State ID' }
  ];

  // Handle next button for each step
  const handleNext = () => {
    setValidationError(null);

    if (currentStep === 'account') {
      // Validate account information
      if (!firstName || !lastName || !email || !password || !phone) {
        setValidationError('Please fill in all required fields');
        return;
      }

      if (!isValidPassword(password)) {
        setValidationError('Password must be at least 8 characters and include a number and special character');
        return;
      }

      if (!agreeToTerms) {
        setValidationError('You must agree to the terms of service');
        return;
      }

      setCurrentStep('bank');
    } else if (currentStep === 'bank') {
      // For simplicity, we'll allow proceeding without validating bank details
      setCurrentStep('profile');
    } else if (currentStep === 'profile') {
      // Validate investment profile
      if (!accountType || !investmentGoal || !riskTolerance || !aiManaged) {
        setValidationError('Please select all investment profile options');
        return;
      }
      setCurrentStep('identity');
    } else if (currentStep === 'identity') {
      // Validate identity verification
      if (!ssn || !dob || !streetAddress || !city || !state || !zipCode || !idType) {
        setValidationError('Please fill in all required fields');
        return;
      }

      if (!certifyInfo) {
        setValidationError('You must certify that all information provided is accurate');
        return;
      }

      // Complete registration
      handleCompleteRegistration();
    }
  };

  // Handle back button
  const handleBack = () => {
    if (currentStep === 'bank') {
      setCurrentStep('account');
    } else if (currentStep === 'profile') {
      setCurrentStep('bank');
    } else if (currentStep === 'identity') {
      setCurrentStep('profile');
    }
  };

  // Complete registration process
  const handleCompleteRegistration = async () => {
    try {
      // Register the user with their account details
      await register(email, password, `${firstName} ${lastName}`);
      
      // Normally you would also submit all the additional information here
      // such as bank details, investment profile, and identity verification
      
      // Redirect to dashboard after successful registration
      navigate('/dashboard');
    } catch (err) {
      console.error('Registration failed:', err);
      setValidationError('There was an error completing your registration');
    }
  };
  
  // Function to select a risk option
  const selectOption = (optionType: string, optionId: string) => {
    if (optionType === 'accountType') {
      setAccountTypeValue(optionId);
    } else if (optionType === 'investmentGoal') {
      setInvestmentGoal(optionId);
    } else if (optionType === 'riskTolerance') {
      setRiskTolerance(optionId);
    } else if (optionType === 'aiManaged') {
      setAiManaged(optionId);
    }
  };

  // Render option card for investment profile selections
  const renderOptionCard = (optionType: string, option: RiskOption, selectedValue: string) => {
    const isSelected = selectedValue === option.id;
    
    return (
      <div 
        key={option.id}
        className={`border border-gray-700 bg-gray-800 rounded-xl p-5 cursor-pointer transition-all ${
          isSelected ? 'border-purple-600 bg-purple-900 bg-opacity-15' : 'hover:border-purple-600 hover:bg-opacity-10'
        }`}
        onClick={() => selectOption(optionType, option.id)}
      >
        <div className="flex justify-between items-start mb-2">
          <h4 className="text-white font-medium">{option.title}</h4>
          {isSelected && (
            <svg className="h-5 w-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
            </svg>
          )}
        </div>
        {option.description && (
          <p className="text-gray-400 text-sm">{option.description}</p>
        )}
      </div>
    );
  };

  // Get step number for progress display
  const getStepNumber = (step: Step): number => {
    const steps: Record<Step, number> = {
      account: 1,
      bank: 2,
      profile: 3,
      identity: 4
    };
    return steps[step];
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Navigation */}
      <nav className="bg-gray-900 shadow-sm w-full">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="text-2xl font-bold">
                <span className="text-purple-400">Elson</span>
              </div>
            </div>
            <div className="flex items-center">
              <Link to="/login" className="text-gray-300 hover:text-white px-3 py-2 text-sm font-medium">
                Already have an account? Log In
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex-grow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Form Progress Indicator */}
          <div className="flex items-center justify-between mb-12">
            {(['account', 'bank', 'profile', 'identity'] as Step[]).map((step, index) => (
              <React.Fragment key={step}>
                <div 
                  className={`flex items-center ${
                    currentStep === step 
                      ? 'text-purple-400' 
                      : getStepNumber(currentStep) > getStepNumber(step)
                      ? 'text-purple-700'
                      : 'text-gray-500'
                  }`}
                >
                  <div 
                    className={`h-8 w-8 rounded-full border-2 flex items-center justify-center mr-2 ${
                      currentStep === step 
                        ? 'border-purple-400 bg-purple-900 text-white' 
                        : getStepNumber(currentStep) > getStepNumber(step)
                        ? 'border-purple-700 bg-purple-900 text-white'
                        : 'border-gray-600 bg-gray-800'
                    }`}
                  >
                    {getStepNumber(currentStep) > getStepNumber(step) ? (
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      getStepNumber(step)
                    )}
                  </div>
                  <span className="hidden sm:inline">{
                    step === 'account' ? 'Account' : 
                    step === 'bank' ? 'Bank Connection' :
                    step === 'profile' ? 'Investment Profile' :
                    'Verify Identity'
                  }</span>
                </div>
                
                {/* Connector line between steps */}
                {index < 3 && (
                  <div 
                    className={`flex-grow h-0.5 mx-2 ${
                      getStepNumber(currentStep) > getStepNumber(step) + 1
                        ? 'bg-purple-700'
                        : 'bg-gray-600'
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Step 1: Account Details */}
          {currentStep === 'account' && (
            <div className="space-y-6">
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">Create your Elson account</h2>
                <p className="text-gray-400">Let's start by setting up your login details</p>
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

              <Input
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a secure password"
                helperText="Password must be at least 8 characters and include a number and special character"
                required
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
                    I agree to Elson's <a href="#" className="text-purple-400 hover:text-purple-300">Terms of Service</a> and <a href="#" className="text-purple-400 hover:text-purple-300">Privacy Policy</a>
                  </span>
                </label>
              </div>

              {(error || validationError) && (
                <div className="text-red-500 text-sm">
                  {error || validationError}
                </div>
              )}

              <div className="flex justify-end pt-6">
                <Button
                  variant="primary"
                  onClick={handleNext}
                  isLoading={loading}
                >
                  Continue
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: Bank Connection */}
          {currentStep === 'bank' && (
            <div className="space-y-6">
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">Connect your bank account</h2>
                <p className="text-gray-400">Securely link your bank to fund your investments</p>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 mb-8">
                <div className="flex items-start">
                  <div className="h-10 w-10 bg-purple-900 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="h-5 w-5 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                    </svg>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-white font-medium mb-1">Bank-level Security</h3>
                    <p className="text-gray-400 text-sm">Elson uses 256-bit encryption and never stores your banking credentials. We use Plaid to securely connect to your bank.</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {bankOptions.map(bank => (
                  <div 
                    key={bank.name}
                    className="bg-gray-800 p-4 rounded-xl flex flex-col items-center justify-center cursor-pointer hover:bg-gray-700 transition-colors"
                    onClick={() => setBankName(bank.name)}
                  >
                    <div className="text-3xl mb-2">{bank.logo}</div>
                    <span className="text-sm text-gray-300">{bank.name}</span>
                  </div>
                ))}
              </div>

              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 mt-6">
                <h4 className="text-white font-medium mb-2">Manual Account Setup</h4>
                <p className="text-gray-400 text-sm mb-4">Prefer to set up manually? Enter your account details below.</p>

                <div className="space-y-4">
                  <Input
                    label="Bank Name"
                    type="text"
                    value={bankName}
                    onChange={(e) => setBankName(e.target.value)}
                    placeholder="Enter your bank name"
                  />

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                      label="Routing Number"
                      type="text"
                      value={routingNumber}
                      onChange={(e) => setRoutingNumber(e.target.value)}
                      placeholder="000000000"
                    />
                    <Input
                      label="Account Number"
                      type="text"
                      value={accountNumber}
                      onChange={(e) => setAccountNumber(e.target.value)}
                      placeholder="00000000000"
                    />
                  </div>

                  <Select
                    label="Account Type"
                    value={accountType}
                    onChange={(value) => setAccountType(value)}
                    options={[
                      { value: 'checking', label: 'Checking' },
                      { value: 'savings', label: 'Savings' }
                    ]}
                    placeholder="Select account type"
                  />
                </div>
              </div>

              {validationError && (
                <div className="text-red-500 text-sm">
                  {validationError}
                </div>
              )}

              <div className="flex justify-between pt-6">
                <Button
                  variant="secondary"
                  onClick={handleBack}
                >
                  Back
                </Button>
                <Button
                  variant="primary"
                  onClick={handleNext}
                  isLoading={loading}
                >
                  Continue
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Investment Profile */}
          {currentStep === 'profile' && (
            <div className="space-y-8">
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">Set your investment profile</h2>
                <p className="text-gray-400">Help us customize your experience based on your investment goals</p>
              </div>

              <div>
                <h3 className="text-lg font-medium text-white mb-4">What type of account would you like to open?</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {accountTypeOptions.map(option => renderOptionCard('accountType', option, accountType))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-white mb-4">What is your primary investment goal?</h3>
                <div className="grid grid-cols-1 gap-3">
                  {investmentGoalOptions.map(option => renderOptionCard('investmentGoal', option, investmentGoal))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-white mb-4">What is your risk tolerance?</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {riskToleranceOptions.map(option => renderOptionCard('riskTolerance', option, riskTolerance))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-white mb-4">Would you like our AI to automatically manage your portfolio?</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {aiManagementOptions.map(option => renderOptionCard('aiManaged', option, aiManaged))}
                </div>
              </div>

              {validationError && (
                <div className="text-red-500 text-sm">
                  {validationError}
                </div>
              )}

              <div className="flex justify-between pt-6">
                <Button
                  variant="secondary"
                  onClick={handleBack}
                >
                  Back
                </Button>
                <Button
                  variant="primary"
                  onClick={handleNext}
                  isLoading={loading}
                >
                  Continue
                </Button>
              </div>
            </div>
          )}

          {/* Step 4: Identity Verification */}
          {currentStep === 'identity' && (
            <div className="space-y-6">
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">Verify your identity</h2>
                <p className="text-gray-400">As required by regulations, we need to verify your identity</p>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 mb-8">
                <div className="flex items-start">
                  <div className="h-10 w-10 bg-purple-900 rounded-full flex items-center justify-center flex-shrink-0">
                    <svg className="h-5 w-5 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-white font-medium mb-1">Why we need this information</h3>
                    <p className="text-gray-400 text-sm">To comply with KYC (Know Your Customer) and AML (Anti-Money Laundering) regulations, we need to verify your identity. Your information is encrypted and secure.</p>
                  </div>
                </div>
              </div>

              <Input
                label="Social Security Number"
                type="text"
                value={ssn}
                onChange={(e) => setSsn(e.target.value)}
                placeholder="XXX-XX-XXXX"
                required
              />

              <Input
                label="Date of Birth"
                type="text"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                placeholder="MM/DD/YYYY"
                required
              />

              <div className="space-y-4">
                <label className="block text-sm font-medium text-gray-400">Home Address</label>
                <Input
                  type="text"
                  value={streetAddress}
                  onChange={(e) => setStreetAddress(e.target.value)}
                  placeholder="Street Address"
                  required
                />
                <Input
                  type="text"
                  value={aptSuite}
                  onChange={(e) => setAptSuite(e.target.value)}
                  placeholder="Apt, Suite, etc. (optional)"
                />
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    type="text"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder="City"
                    required
                  />
                  <Input
                    type="text"
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    placeholder="State"
                    required
                  />
                </div>
                <Input
                  type="text"
                  value={zipCode}
                  onChange={(e) => setZipCode(e.target.value)}
                  placeholder="ZIP Code"
                  required
                />
              </div>

              <Select
                label="ID Type"
                value={idType}
                onChange={(value) => setIdType(value)}
                options={idTypeOptions}
                placeholder="Select ID type"
                required
              />

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Upload ID Document (Front)</label>
                <div className="border-2 border-dashed border-gray-700 rounded-lg p-6 text-center">
                  <svg className="h-10 w-10 text-gray-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                  <p className="text-gray-400 text-sm mb-2">Drag and drop your file here, or click to browse</p>
                  <Button variant="secondary" size="sm">Browse Files</Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Upload ID Document (Back)</label>
                <div className="border-2 border-dashed border-gray-700 rounded-lg p-6 text-center">
                  <svg className="h-10 w-10 text-gray-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                  <p className="text-gray-400 text-sm mb-2">Drag and drop your file here, or click to browse</p>
                  <Button variant="secondary" size="sm">Browse Files</Button>
                </div>
              </div>

              <div className="mt-4">
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    className="h-4 w-4 text-purple-600 rounded border-gray-700 focus:ring-purple-500"
                    checked={certifyInfo}
                    onChange={(e) => setCertifyInfo(e.target.checked)}
                  />
                  <span className="ml-2 text-sm text-gray-400">
                    I certify that all information provided is accurate and complete.
                  </span>
                </label>
              </div>

              {(error || validationError) && (
                <div className="text-red-500 text-sm">
                  {error || validationError}
                </div>
              )}

              <div className="flex justify-between pt-6">
                <Button
                  variant="secondary"
                  onClick={handleBack}
                >
                  Back
                </Button>
                <Button
                  variant="primary"
                  onClick={handleNext}
                  isLoading={loading}
                >
                  Complete Account Setup
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}