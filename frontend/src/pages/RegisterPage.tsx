import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { unwrapResult } from '@reduxjs/toolkit';
import { RootState } from '../store/store';
import { register, clearError } from '../store/slices/authSlice';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

const REGISTRATION_STORAGE_KEY = 'elson_registration_draft';
const STORAGE_EXPIRY_HOURS = 24;

interface FormData {
  // Step 1: Personal Info
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  password: string;
  confirmPassword: string;

  // Step 2: Identity Verification
  dateOfBirth: string;
  ssn: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;

  // Step 3: Investment Profile
  employmentStatus: string;
  annualIncome: string;
  netWorth: string;
  investmentExperience: string;

  // Step 4: Risk Assessment
  riskTolerance: string;
  investmentGoals: string[];
  timeHorizon: string;

  // Step 5: Review & Agreement
  agreeToTerms: boolean;
  agreeToPrivacy: boolean;
  agreeToElectronic: boolean;
}

const RegisterPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isLoading, error } = useSelector((state: RootState) => state.auth);

  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 5;
  const [showSuccess, setShowSuccess] = useState(false);

  const [formData, setFormData] = useState<FormData>(() => {
    // Try to load saved draft from localStorage
    const savedDraft = localStorage.getItem(REGISTRATION_STORAGE_KEY);
    if (savedDraft) {
      try {
        const { data, timestamp } = JSON.parse(savedDraft);
        const age = Date.now() - timestamp;
        const maxAge = STORAGE_EXPIRY_HOURS * 60 * 60 * 1000;

        if (age < maxAge) {
          return data;
        } else {
          localStorage.removeItem(REGISTRATION_STORAGE_KEY);
        }
      } catch (e) {
        console.error('Failed to load registration draft:', e);
      }
    }

    return {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      password: '',
      confirmPassword: '',
      dateOfBirth: '',
      ssn: '',
      address: '',
      city: '',
      state: '',
      zipCode: '',
      employmentStatus: '',
      annualIncome: '',
      netWorth: '',
      investmentExperience: '',
      riskTolerance: 'moderate',
      investmentGoals: [],
      timeHorizon: '',
      agreeToTerms: false,
      agreeToPrivacy: false,
      agreeToElectronic: false
    };
  });

  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Only clear field-specific validation error
    if (formErrors[name]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }));
    }

    // Only clear global auth error when editing email/password
    if (error && (name === 'email' || name === 'password')) {
      dispatch(clearError());
    }
  };

  // Save form data to localStorage (excluding sensitive data)
  useEffect(() => {
    const hasData = formData.firstName || formData.lastName || formData.email;

    if (hasData) {
      const dataToSave = {
        ...formData,
        password: '',        // Never save sensitive data
        confirmPassword: '',
        ssn: ''
      };

      try {
        const draftData = {
          data: dataToSave,
          timestamp: Date.now()
        };
        localStorage.setItem(REGISTRATION_STORAGE_KEY, JSON.stringify(draftData));
      } catch (e) {
        console.warn('Could not save registration draft:', e);
      }
    }
  }, [formData]);

  const handleGoalToggle = (goal: string) => {
    setFormData(prev => ({
      ...prev,
      investmentGoals: prev.investmentGoals.includes(goal)
        ? prev.investmentGoals.filter(g => g !== goal)
        : [...prev.investmentGoals, goal]
    }));
  };

  const validateStep = (step: number): boolean => {
    const errors: { [key: string]: string } = {};

    switch (step) {
      case 1:
        if (!formData.firstName) errors.firstName = 'First name is required';
        if (!formData.lastName) errors.lastName = 'Last name is required';
        if (!formData.email) errors.email = 'Email is required';
        else if (!/\S+@\S+\.\S+/.test(formData.email)) errors.email = 'Email is invalid';
        if (!formData.phone) errors.phone = 'Phone number is required';
        if (!formData.password) errors.password = 'Password is required';
        else if (formData.password.length < 8) errors.password = 'Password must be at least 8 characters';
        if (formData.password !== formData.confirmPassword) errors.confirmPassword = 'Passwords do not match';
        break;
      case 2:
        if (!formData.dateOfBirth) errors.dateOfBirth = 'Date of birth is required';
        if (!formData.ssn) errors.ssn = 'SSN is required';
        if (!formData.address) errors.address = 'Address is required';
        if (!formData.city) errors.city = 'City is required';
        if (!formData.state) errors.state = 'State is required';
        if (!formData.zipCode) errors.zipCode = 'ZIP code is required';
        break;
      case 3:
        if (!formData.employmentStatus) errors.employmentStatus = 'Employment status is required';
        if (!formData.annualIncome) errors.annualIncome = 'Annual income is required';
        break;
      case 4:
        if (!formData.riskTolerance) errors.riskTolerance = 'Risk tolerance is required';
        if (!formData.timeHorizon) errors.timeHorizon = 'Time horizon is required';
        break;
      case 5:
        if (!formData.agreeToTerms) errors.agreeToTerms = 'You must agree to the terms';
        if (!formData.agreeToPrivacy) errors.agreeToPrivacy = 'You must agree to the privacy policy';
        if (!formData.agreeToElectronic) errors.agreeToElectronic = 'You must agree to electronic communications';
        break;
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, totalSteps));
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateStep(currentStep)) return;

    const userData = {
      email: formData.email,
      password: formData.password,
      full_name: `${formData.firstName} ${formData.lastName}`,
      risk_tolerance: formData.riskTolerance,
      trading_style: 'long_term'
    };

    try {
      const resultAction = await dispatch(register(userData) as any);
      const user = unwrapResult(resultAction);

      // Registration succeeded - clear draft and show success
      localStorage.removeItem(REGISTRATION_STORAGE_KEY);
      setShowSuccess(true);

      // Navigate after short delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (error) {
      // Error already shown by Redux state via error banner
      console.error('Registration failed:', error);
    }
  };

  const stepTitles = [
    'Personal Information',
    'Identity Verification',
    'Investment Profile',
    'Risk Assessment',
    'Review & Submit'
  ];

  const renderProgressBar = () => (
    <div className="mb-8">
      <div className="flex justify-between mb-2">
        {stepTitles.map((title, index) => (
          <div
            key={index}
            className={`flex-1 text-center text-xs ${
              index + 1 <= currentStep ? 'text-purple-400' : 'text-gray-500'
            }`}
          >
            <div
              className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center mb-1 ${
                index + 1 < currentStep
                  ? 'bg-purple-600 text-white'
                  : index + 1 === currentStep
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-400'
              }`}
            >
              {index + 1 < currentStep ? (
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span className="hidden md:block">{title}</span>
          </div>
        ))}
      </div>
      <div className="h-2 bg-gray-700 rounded-full">
        <div
          className="h-2 bg-purple-600 rounded-full transition-all duration-300"
          style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
        />
      </div>
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-gray-300 text-sm mb-1">First Name *</label>
          <input
            type="text"
            name="firstName"
            value={formData.firstName}
            onChange={handleChange}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
            placeholder="Enter first name"
          />
          {formErrors.firstName && <p className="text-red-400 text-xs mt-1">{formErrors.firstName}</p>}
        </div>
        <div>
          <label className="block text-gray-300 text-sm mb-1">Last Name *</label>
          <input
            type="text"
            name="lastName"
            value={formData.lastName}
            onChange={handleChange}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
            placeholder="Enter last name"
          />
          {formErrors.lastName && <p className="text-red-400 text-xs mt-1">{formErrors.lastName}</p>}
        </div>
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Email Address *</label>
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          placeholder="Enter email address"
        />
        {formErrors.email && <p className="text-red-400 text-xs mt-1">{formErrors.email}</p>}
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Phone Number *</label>
        <input
          type="tel"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          placeholder="(555) 123-4567"
        />
        {formErrors.phone && <p className="text-red-400 text-xs mt-1">{formErrors.phone}</p>}
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Password *</label>
        <input
          type="password"
          name="password"
          value={formData.password}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          placeholder="Create a strong password"
        />
        {formErrors.password && <p className="text-red-400 text-xs mt-1">{formErrors.password}</p>}
        <p className="text-gray-500 text-xs mt-1">Must be at least 8 characters</p>
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Confirm Password *</label>
        <input
          type="password"
          name="confirmPassword"
          value={formData.confirmPassword}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          placeholder="Confirm your password"
        />
        {formErrors.confirmPassword && <p className="text-red-400 text-xs mt-1">{formErrors.confirmPassword}</p>}
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-4">
      <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <svg className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <div>
            <p className="text-yellow-200 text-sm font-medium">Secure Verification</p>
            <p className="text-yellow-200/70 text-xs">Your information is encrypted and protected. Required by law for all investment accounts.</p>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Date of Birth *</label>
        <input
          type="date"
          name="dateOfBirth"
          value={formData.dateOfBirth}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
        />
        {formErrors.dateOfBirth && <p className="text-red-400 text-xs mt-1">{formErrors.dateOfBirth}</p>}
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Social Security Number *</label>
        <input
          type="password"
          name="ssn"
          value={formData.ssn}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          placeholder="XXX-XX-XXXX"
        />
        {formErrors.ssn && <p className="text-red-400 text-xs mt-1">{formErrors.ssn}</p>}
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Street Address *</label>
        <input
          type="text"
          name="address"
          value={formData.address}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          placeholder="Enter your street address"
        />
        {formErrors.address && <p className="text-red-400 text-xs mt-1">{formErrors.address}</p>}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-gray-300 text-sm mb-1">City *</label>
          <input
            type="text"
            name="city"
            value={formData.city}
            onChange={handleChange}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
            placeholder="City"
          />
          {formErrors.city && <p className="text-red-400 text-xs mt-1">{formErrors.city}</p>}
        </div>
        <div>
          <label className="block text-gray-300 text-sm mb-1">State *</label>
          <select
            name="state"
            value={formData.state}
            onChange={handleChange}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          >
            <option value="">Select</option>
            <option value="AL">Alabama</option>
            <option value="AK">Alaska</option>
            <option value="AZ">Arizona</option>
            <option value="AR">Arkansas</option>
            <option value="CA">California</option>
            <option value="CO">Colorado</option>
            <option value="CT">Connecticut</option>
            <option value="DE">Delaware</option>
            <option value="FL">Florida</option>
            <option value="GA">Georgia</option>
            <option value="HI">Hawaii</option>
            <option value="ID">Idaho</option>
            <option value="IL">Illinois</option>
            <option value="IN">Indiana</option>
            <option value="IA">Iowa</option>
            <option value="KS">Kansas</option>
            <option value="KY">Kentucky</option>
            <option value="LA">Louisiana</option>
            <option value="ME">Maine</option>
            <option value="MD">Maryland</option>
            <option value="MA">Massachusetts</option>
            <option value="MI">Michigan</option>
            <option value="MN">Minnesota</option>
            <option value="MS">Mississippi</option>
            <option value="MO">Missouri</option>
            <option value="MT">Montana</option>
            <option value="NE">Nebraska</option>
            <option value="NV">Nevada</option>
            <option value="NH">New Hampshire</option>
            <option value="NJ">New Jersey</option>
            <option value="NM">New Mexico</option>
            <option value="NY">New York</option>
            <option value="NC">North Carolina</option>
            <option value="ND">North Dakota</option>
            <option value="OH">Ohio</option>
            <option value="OK">Oklahoma</option>
            <option value="OR">Oregon</option>
            <option value="PA">Pennsylvania</option>
            <option value="RI">Rhode Island</option>
            <option value="SC">South Carolina</option>
            <option value="SD">South Dakota</option>
            <option value="TN">Tennessee</option>
            <option value="TX">Texas</option>
            <option value="UT">Utah</option>
            <option value="VT">Vermont</option>
            <option value="VA">Virginia</option>
            <option value="WA">Washington</option>
            <option value="WV">West Virginia</option>
            <option value="WI">Wisconsin</option>
            <option value="WY">Wyoming</option>
          </select>
          {formErrors.state && <p className="text-red-400 text-xs mt-1">{formErrors.state}</p>}
        </div>
        <div>
          <label className="block text-gray-300 text-sm mb-1">ZIP Code *</label>
          <input
            type="text"
            name="zipCode"
            value={formData.zipCode}
            onChange={handleChange}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
            placeholder="12345"
          />
          {formErrors.zipCode && <p className="text-red-400 text-xs mt-1">{formErrors.zipCode}</p>}
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-gray-300 text-sm mb-1">Employment Status *</label>
        <select
          name="employmentStatus"
          value={formData.employmentStatus}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
        >
          <option value="">Select employment status</option>
          <option value="employed">Employed</option>
          <option value="self-employed">Self-Employed</option>
          <option value="retired">Retired</option>
          <option value="student">Student</option>
          <option value="unemployed">Unemployed</option>
        </select>
        {formErrors.employmentStatus && <p className="text-red-400 text-xs mt-1">{formErrors.employmentStatus}</p>}
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Annual Income *</label>
        <select
          name="annualIncome"
          value={formData.annualIncome}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
        >
          <option value="">Select annual income</option>
          <option value="0-25000">$0 - $25,000</option>
          <option value="25000-50000">$25,000 - $50,000</option>
          <option value="50000-100000">$50,000 - $100,000</option>
          <option value="100000-200000">$100,000 - $200,000</option>
          <option value="200000+">$200,000+</option>
        </select>
        {formErrors.annualIncome && <p className="text-red-400 text-xs mt-1">{formErrors.annualIncome}</p>}
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Net Worth</label>
        <select
          name="netWorth"
          value={formData.netWorth}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
        >
          <option value="">Select net worth</option>
          <option value="0-50000">$0 - $50,000</option>
          <option value="50000-100000">$50,000 - $100,000</option>
          <option value="100000-500000">$100,000 - $500,000</option>
          <option value="500000-1000000">$500,000 - $1,000,000</option>
          <option value="1000000+">$1,000,000+</option>
        </select>
      </div>

      <div>
        <label className="block text-gray-300 text-sm mb-1">Investment Experience</label>
        <select
          name="investmentExperience"
          value={formData.investmentExperience}
          onChange={handleChange}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
        >
          <option value="">Select experience level</option>
          <option value="none">None</option>
          <option value="beginner">Beginner (1-2 years)</option>
          <option value="intermediate">Intermediate (3-5 years)</option>
          <option value="experienced">Experienced (5+ years)</option>
        </select>
      </div>
    </div>
  );

  const renderStep4 = () => {
    const goals = [
      'Retirement',
      'Wealth Building',
      'Emergency Fund',
      'Major Purchase',
      'Education',
      'Income Generation'
    ];

    return (
      <div className="space-y-6">
        <div>
          <label className="block text-gray-300 text-sm mb-3">Risk Tolerance *</label>
          <div className="grid grid-cols-3 gap-4">
            {['conservative', 'moderate', 'aggressive'].map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, riskTolerance: level }))}
                className={`p-4 rounded-lg border text-center transition-colors ${
                  formData.riskTolerance === level
                    ? 'border-purple-500 bg-purple-900/30'
                    : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                }`}
              >
                <p className="text-white font-medium capitalize">{level}</p>
                <p className="text-gray-400 text-xs mt-1">
                  {level === 'conservative' && 'Lower risk, steady growth'}
                  {level === 'moderate' && 'Balanced approach'}
                  {level === 'aggressive' && 'Higher risk, higher potential'}
                </p>
              </button>
            ))}
          </div>
          {formErrors.riskTolerance && <p className="text-red-400 text-xs mt-1">{formErrors.riskTolerance}</p>}
        </div>

        <div>
          <label className="block text-gray-300 text-sm mb-3">Investment Goals (select all that apply)</label>
          <div className="grid grid-cols-2 gap-3">
            {goals.map((goal) => (
              <button
                key={goal}
                type="button"
                onClick={() => handleGoalToggle(goal)}
                className={`p-3 rounded-lg border text-left transition-colors ${
                  formData.investmentGoals.includes(goal)
                    ? 'border-purple-500 bg-purple-900/30'
                    : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                }`}
              >
                <span className="text-white text-sm">{goal}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-gray-300 text-sm mb-1">Investment Time Horizon *</label>
          <select
            name="timeHorizon"
            value={formData.timeHorizon}
            onChange={handleChange}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          >
            <option value="">Select time horizon</option>
            <option value="short">Short-term (0-2 years)</option>
            <option value="medium">Medium-term (3-5 years)</option>
            <option value="long">Long-term (5-10 years)</option>
            <option value="verylong">Very long-term (10+ years)</option>
          </select>
          {formErrors.timeHorizon && <p className="text-red-400 text-xs mt-1">{formErrors.timeHorizon}</p>}
        </div>
      </div>
    );
  };

  const renderStep5 = () => (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Review Your Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-400">Name</p>
            <p className="text-white">{formData.firstName} {formData.lastName}</p>
          </div>
          <div>
            <p className="text-gray-400">Email</p>
            <p className="text-white">{formData.email}</p>
          </div>
          <div>
            <p className="text-gray-400">Phone</p>
            <p className="text-white">{formData.phone}</p>
          </div>
          <div>
            <p className="text-gray-400">Risk Tolerance</p>
            <p className="text-white capitalize">{formData.riskTolerance}</p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            name="agreeToTerms"
            checked={formData.agreeToTerms}
            onChange={handleChange}
            className="mt-1 h-4 w-4 rounded border-gray-700 bg-gray-800 text-purple-600 focus:ring-purple-500"
          />
          <span className="text-gray-300 text-sm">
            I agree to the <a href="#" className="text-purple-400 hover:text-purple-300">Terms of Service</a> and <a href="#" className="text-purple-400 hover:text-purple-300">Customer Agreement</a>
          </span>
        </label>
        {formErrors.agreeToTerms && <p className="text-red-400 text-xs ml-7">{formErrors.agreeToTerms}</p>}

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            name="agreeToPrivacy"
            checked={formData.agreeToPrivacy}
            onChange={handleChange}
            className="mt-1 h-4 w-4 rounded border-gray-700 bg-gray-800 text-purple-600 focus:ring-purple-500"
          />
          <span className="text-gray-300 text-sm">
            I agree to the <a href="#" className="text-purple-400 hover:text-purple-300">Privacy Policy</a>
          </span>
        </label>
        {formErrors.agreeToPrivacy && <p className="text-red-400 text-xs ml-7">{formErrors.agreeToPrivacy}</p>}

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            name="agreeToElectronic"
            checked={formData.agreeToElectronic}
            onChange={handleChange}
            className="mt-1 h-4 w-4 rounded border-gray-700 bg-gray-800 text-purple-600 focus:ring-purple-500"
          />
          <span className="text-gray-300 text-sm">
            I consent to receive electronic communications and disclosures
          </span>
        </label>
        {formErrors.agreeToElectronic && <p className="text-red-400 text-xs ml-7">{formErrors.agreeToElectronic}</p>}
      </div>
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return renderStep1();
      case 2: return renderStep2();
      case 3: return renderStep3();
      case 4: return renderStep4();
      case 5: return renderStep5();
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center py-12 px-4">
      <div className="max-w-lg w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center">
            <div className="h-12 w-12 rounded-lg bg-gradient-to-r from-purple-600 to-blue-500 flex items-center justify-center">
              <span className="text-white font-bold text-2xl">E</span>
            </div>
            <span className="ml-3 text-2xl font-bold text-white">Elson</span>
          </Link>
        </div>

        <div className="bg-gray-800 rounded-2xl p-8 border border-gray-700">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-white">Create Your Account</h1>
            <p className="text-gray-400 mt-2">Step {currentStep} of {totalSteps}: {stepTitles[currentStep - 1]}</p>
          </div>

          {renderProgressBar()}

          {showSuccess && (
            <div className="bg-green-900/30 border border-green-700 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-3">
                <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <p className="text-green-400 text-sm font-medium">Account created successfully! Redirecting...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {renderCurrentStep()}

            <div className="flex gap-4 mt-8">
              {currentStep > 1 && (
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg transition-colors"
                >
                  Back
                </button>
              )}
              {currentStep < totalSteps ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition-colors"
                >
                  Continue
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg transition-colors disabled:opacity-50"
                >
                  {isLoading ? <LoadingSpinner size="sm" /> : 'Create Account'}
                </button>
              )}
            </div>
          </form>

          <div className="text-center mt-6">
            <p className="text-gray-400 text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-purple-400 hover:text-purple-300">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        <p className="text-center text-gray-500 text-xs mt-6">
          By creating an account, you agree to our Terms of Service and Privacy Policy.
          Securities offered through Elson Securities LLC, Member FINRA/SIPC.
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
