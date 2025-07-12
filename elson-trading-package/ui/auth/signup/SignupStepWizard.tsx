import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../common/Button';
import AccountDetailsStep from './AccountDetailsStep';
import BankConnectionStep from './BankConnectionStep';
import InvestmentProfileStep from './InvestmentProfileStep';
import IdentityVerificationStep from './IdentityVerificationStep';
import { useAuth } from '../../../hooks/useAuth';

// Step types to track onboarding process
type Step = 'account' | 'bank' | 'profile' | 'identity' | 'complete';

interface SignupStepWizardProps {
  initialStep?: Step;
}

const SignupStepWizard: React.FC<SignupStepWizardProps> = ({ initialStep = 'account' }) => {
  const { register, loading, error } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<Step>(initialStep);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Step 1: Account Details
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [agreeToTerms, setAgreeToTerms] = useState(false);

  // Step 2: Bank Connection
  const [bankName, setBankName] = useState('');
  const [routingNumber, setRoutingNumber] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [accountType, setAccountType] = useState('');

  // Step 3: Investment Profile
  const [accountTypeValue, setAccountTypeValue] = useState<string>('');
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

  // Validate the current step
  const validateStep = () => {
    setValidationError(null);

    if (currentStep === 'account') {
      // Validate account information
      if (!firstName || !lastName || !email || !password || !confirmPassword || !phone) {
        setValidationError('Please fill in all required fields');
        return false;
      }

      if (password !== confirmPassword) {
        setValidationError('Passwords do not match');
        return false;
      }

      if (password.length < 8) {
        setValidationError('Password must be at least 8 characters');
        return false;
      }

      if (!/[A-Z]/.test(password)) {
        setValidationError('Password must contain at least one uppercase letter');
        return false;
      }

      if (!/[a-z]/.test(password)) {
        setValidationError('Password must contain at least one lowercase letter');
        return false;
      }

      if (!/[0-9]/.test(password)) {
        setValidationError('Password must contain at least one number');
        return false;
      }

      if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password)) {
        setValidationError('Password must contain at least one special character');
        return false;
      }

      if (!agreeToTerms) {
        setValidationError('You must agree to the terms of service');
        return false;
      }

      return true;
    } 
    else if (currentStep === 'bank') {
      // Bank info is optional for now
      return true;
    } 
    else if (currentStep === 'profile') {
      // Validate investment profile
      if (!accountTypeValue || !investmentGoal || !riskTolerance || !aiManaged) {
        setValidationError('Please select all investment profile options');
        return false;
      }
      return true;
    } 
    else if (currentStep === 'identity') {
      // Validate identity verification
      if (!ssn || !dob || !streetAddress || !city || !state || !zipCode || !idType) {
        setValidationError('Please fill in all required fields');
        return false;
      }

      if (!certifyInfo) {
        setValidationError('You must certify that all information provided is accurate');
        return false;
      }

      return true;
    }

    return true;
  };

  // Handle next button for each step
  const handleNext = () => {
    if (validateStep()) {
      if (currentStep === 'account') {
        setCurrentStep('bank');
      } else if (currentStep === 'bank') {
        setCurrentStep('profile');
      } else if (currentStep === 'profile') {
        setCurrentStep('identity');
      } else if (currentStep === 'identity') {
        handleCompleteRegistration();
      }
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
      
      // Redirect to welcome onboarding after successful registration
      navigate('/welcome');
    } catch (err) {
      console.error('Registration failed:', err);
      setValidationError('There was an error completing your registration');
    }
  };

  // Skip the current step (only applicable for bank step)
  const handleSkip = () => {
    if (currentStep === 'bank') {
      setCurrentStep('profile');
    }
  };

  // Get step number for progress display
  const getStepNumber = (step: Step): number => {
    const steps: Record<Step, number> = {
      account: 1,
      bank: 2,
      profile: 3,
      identity: 4,
      complete: 5
    };
    return steps[step];
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Form Progress Indicator */}
      <div className="w-full bg-gray-800 pt-4 pb-4">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
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
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-grow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Step 1: Account Details */}
          {currentStep === 'account' && (
            <AccountDetailsStep
              firstName={firstName}
              lastName={lastName}
              email={email}
              password={password}
              confirmPassword={confirmPassword}
              phone={phone}
              agreeToTerms={agreeToTerms}
              setFirstName={setFirstName}
              setLastName={setLastName}
              setEmail={setEmail}
              setPassword={setPassword}
              setConfirmPassword={setConfirmPassword}
              setPhone={setPhone}
              setAgreeToTerms={setAgreeToTerms}
              validationError={validationError || error}
              validateStep={validateStep}
            />
          )}

          {/* Step 2: Bank Connection */}
          {currentStep === 'bank' && (
            <BankConnectionStep
              bankName={bankName}
              routingNumber={routingNumber}
              accountNumber={accountNumber}
              accountType={accountType}
              setBankName={setBankName}
              setRoutingNumber={setRoutingNumber}
              setAccountNumber={setAccountNumber}
              setAccountType={setAccountType}
              validationError={validationError}
              validateStep={validateStep}
            />
          )}

          {/* Step 3: Investment Profile */}
          {currentStep === 'profile' && (
            <InvestmentProfileStep
              accountType={accountTypeValue}
              investmentGoal={investmentGoal}
              riskTolerance={riskTolerance}
              aiManaged={aiManaged}
              setAccountType={setAccountTypeValue}
              setInvestmentGoal={setInvestmentGoal}
              setRiskTolerance={setRiskTolerance}
              setAiManaged={setAiManaged}
              validationError={validationError}
              validateStep={validateStep}
            />
          )}

          {/* Step 4: Identity Verification */}
          {currentStep === 'identity' && (
            <IdentityVerificationStep
              ssn={ssn}
              dob={dob}
              streetAddress={streetAddress}
              aptSuite={aptSuite}
              city={city}
              state={state}
              zipCode={zipCode}
              idType={idType}
              certifyInfo={certifyInfo}
              setSsn={setSsn}
              setDob={setDob}
              setStreetAddress={setStreetAddress}
              setAptSuite={setAptSuite}
              setCity={setCity}
              setState={setState}
              setZipCode={setZipCode}
              setIdType={setIdType}
              setCertifyInfo={setCertifyInfo}
              validationError={validationError}
              validateStep={validateStep}
            />
          )}

          <div className="flex justify-between pt-6">
            {currentStep !== 'account' && (
              <Button
                variant="secondary"
                onClick={handleBack}
              >
                Back
              </Button>
            )}
            
            {currentStep === 'account' && (
              <div></div> // Empty div to maintain flex spacing
            )}

            <div className="flex space-x-4">
              {currentStep === 'bank' && (
                <Button
                  variant="text"
                  onClick={handleSkip}
                >
                  Skip for now
                </Button>
              )}
              
              <Button
                variant="primary"
                onClick={handleNext}
                isLoading={loading}
              >
                {currentStep === 'identity' ? 'Complete Registration' : 'Continue'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupStepWizard;