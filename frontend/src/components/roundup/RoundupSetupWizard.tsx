import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { api } from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

// Types matching backend schemas
interface RoundupSettings {
  roundup_enabled: boolean;
  roundup_multiplier: number;
  roundup_frequency: 'daily' | 'weekly' | 'threshold';
  roundup_threshold: number;
  micro_invest_target_type: 'default_portfolio' | 'specific_portfolio' | 'specific_symbol' | 'recommended_etf';
  micro_invest_portfolio_id?: number;
  micro_invest_symbol?: string;
  notify_on_roundup: boolean;
  notify_on_investment: boolean;
  max_weekly_roundup: number;
}

interface Portfolio {
  id: number;
  name: string;
}

interface RoundupSetupWizardProps {
  darkMode?: boolean;
  onComplete?: () => void;
  onCancel?: () => void;
}

// Recommended ETFs for round-up investing
const RECOMMENDED_ETFS = [
  { symbol: 'VTI', name: 'Vanguard Total Stock Market', description: 'Broad US market exposure' },
  { symbol: 'VOO', name: 'Vanguard S&P 500', description: 'Large-cap US stocks' },
  { symbol: 'VGT', name: 'Vanguard Information Technology', description: 'Tech sector focus' },
  { symbol: 'QQQ', name: 'Invesco QQQ Trust', description: 'Nasdaq-100 stocks' },
  { symbol: 'VXUS', name: 'Vanguard Total International', description: 'International exposure' },
  { symbol: 'BND', name: 'Vanguard Total Bond Market', description: 'Fixed income stability' },
];

// Multiplier options
const MULTIPLIER_OPTIONS = [
  { value: 1, label: '1x', description: 'Round up to nearest dollar' },
  { value: 2, label: '2x', description: 'Double your round-ups' },
  { value: 3, label: '3x', description: 'Triple your round-ups' },
  { value: 5, label: '5x', description: 'Accelerate your savings' },
  { value: 10, label: '10x', description: 'Maximum boost' },
];

// Frequency options
const FREQUENCY_OPTIONS = [
  { value: 'daily' as const, label: 'Daily', description: 'Invest collected round-ups every day' },
  { value: 'weekly' as const, label: 'Weekly', description: 'Invest collected round-ups every week' },
  { value: 'threshold' as const, label: 'When threshold reached', description: 'Invest when round-ups reach a set amount' },
];

export const RoundupSetupWizard: React.FC<RoundupSetupWizardProps> = ({
  darkMode = true,
  onComplete,
  onCancel,
}) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  // Wizard state
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);

  // Settings state
  const [settings, setSettings] = useState<RoundupSettings>({
    roundup_enabled: true,
    roundup_multiplier: 1,
    roundup_frequency: 'weekly',
    roundup_threshold: 5.0,
    micro_invest_target_type: 'recommended_etf',
    notify_on_roundup: true,
    notify_on_investment: true,
    max_weekly_roundup: 100,
  });

  const [selectedETF, setSelectedETF] = useState<string>('VTI');

  // Load portfolios
  useEffect(() => {
    const fetchPortfolios = async () => {
      try {
        setLoading(true);
        const response = await api.get('/portfolio');
        setPortfolios(response.data || []);
      } catch (err) {
        console.error('Error fetching portfolios:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolios();
  }, []);

  // Step definitions
  const totalSteps = 5;

  // Handle next step
  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  // Handle previous step
  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Handle save settings
  const handleSave = async () => {
    try {
      setSaving(true);

      // Prepare data based on target type
      const dataToSave = {
        ...settings,
        micro_invest_symbol: settings.micro_invest_target_type === 'recommended_etf' || settings.micro_invest_target_type === 'specific_symbol'
          ? (settings.micro_invest_target_type === 'recommended_etf' ? selectedETF : settings.micro_invest_symbol)
          : undefined,
      };

      await api.patch('/micro-invest/settings', dataToSave);

      enqueueSnackbar('Round-up settings saved successfully!', { variant: 'success' });

      if (onComplete) {
        onComplete();
      } else {
        navigate('/settings');
      }
    } catch (err: any) {
      console.error('Error saving settings:', err);
      enqueueSnackbar(err.response?.data?.detail || 'Failed to save settings', { variant: 'error' });
    } finally {
      setSaving(false);
    }
  };

  // Base styles
  const containerClass = darkMode
    ? 'bg-gray-900 text-white'
    : 'bg-white text-gray-800';

  const cardClass = darkMode
    ? 'bg-gray-800 border-gray-700'
    : 'bg-gray-50 border-gray-200';

  const selectedClass = darkMode
    ? 'bg-blue-900 border-blue-500'
    : 'bg-blue-50 border-blue-500';

  const buttonPrimaryClass = 'bg-blue-600 hover:bg-blue-700 text-white';
  const buttonSecondaryClass = darkMode
    ? 'bg-gray-700 hover:bg-gray-600 text-white'
    : 'bg-gray-200 hover:bg-gray-300 text-gray-800';

  // Progress indicator
  const renderProgress = () => (
    <div className="flex justify-center mb-8">
      {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
        <div key={step} className="flex items-center">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center font-medium text-sm ${
              step < currentStep
                ? 'bg-green-500 text-white'
                : step === currentStep
                  ? 'bg-blue-500 text-white'
                  : darkMode
                    ? 'bg-gray-700 text-gray-400'
                    : 'bg-gray-300 text-gray-500'
            }`}
          >
            {step < currentStep ? '✓' : step}
          </div>
          {step < totalSteps && (
            <div
              className={`w-12 h-1 ${
                step < currentStep
                  ? 'bg-green-500'
                  : darkMode
                    ? 'bg-gray-700'
                    : 'bg-gray-300'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );

  // Step 1: Enable round-ups
  const renderStep1 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-center">Enable Round-Ups</h2>
      <p className={`text-center ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
        Automatically round up your purchases and invest the spare change.
      </p>

      <div className="flex flex-col items-center space-y-4">
        <div className={`p-6 rounded-lg border-2 ${cardClass} max-w-md w-full`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium">Round-Ups</h3>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                Turn on to start saving automatically
              </p>
            </div>
            <button
              onClick={() => setSettings({ ...settings, roundup_enabled: !settings.roundup_enabled })}
              className={`relative w-14 h-8 rounded-full transition-colors ${
                settings.roundup_enabled ? 'bg-green-500' : darkMode ? 'bg-gray-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`absolute top-1 w-6 h-6 rounded-full bg-white transition-transform ${
                  settings.roundup_enabled ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Example */}
        <div className={`p-4 rounded-lg ${cardClass} max-w-md w-full`}>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'} mb-2`}>Example:</p>
          <div className="flex justify-between text-sm">
            <span>Purchase: $4.25</span>
            <span>Round-up: $0.75</span>
          </div>
          <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'} mt-2`}>
            The $0.75 goes into your investment account
          </p>
        </div>
      </div>
    </div>
  );

  // Step 2: Choose multiplier
  const renderStep2 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-center">Choose Your Multiplier</h2>
      <p className={`text-center ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
        Boost your savings by multiplying your round-ups.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-lg mx-auto">
        {MULTIPLIER_OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => setSettings({ ...settings, roundup_multiplier: option.value })}
            className={`p-4 rounded-lg border-2 transition-all ${
              settings.roundup_multiplier === option.value
                ? selectedClass
                : `${cardClass} hover:border-blue-400`
            }`}
          >
            <span className="text-2xl font-bold">{option.label}</span>
            <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {option.description}
            </p>
          </button>
        ))}
      </div>

      {/* Preview */}
      <div className={`p-4 rounded-lg ${cardClass} max-w-md mx-auto`}>
        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'} mb-2`}>
          With {settings.roundup_multiplier}x multiplier:
        </p>
        <div className="flex justify-between">
          <span>$0.75 round-up becomes</span>
          <span className="font-bold text-green-500">
            {formatCurrency(0.75 * settings.roundup_multiplier)}
          </span>
        </div>
      </div>
    </div>
  );

  // Step 3: Investment frequency
  const renderStep3 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-center">When to Invest</h2>
      <p className={`text-center ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
        Choose how often to invest your collected round-ups.
      </p>

      <div className="space-y-4 max-w-md mx-auto">
        {FREQUENCY_OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => setSettings({ ...settings, roundup_frequency: option.value })}
            className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
              settings.roundup_frequency === option.value
                ? selectedClass
                : `${cardClass} hover:border-blue-400`
            }`}
          >
            <span className="font-medium">{option.label}</span>
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {option.description}
            </p>
          </button>
        ))}
      </div>

      {/* Threshold input (if threshold selected) */}
      {settings.roundup_frequency === 'threshold' && (
        <div className={`p-4 rounded-lg ${cardClass} max-w-md mx-auto`}>
          <label className="block text-sm font-medium mb-2">
            Investment Threshold
          </label>
          <div className="flex items-center">
            <span className={`mr-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>$</span>
            <input
              type="number"
              min="1"
              max="100"
              value={settings.roundup_threshold}
              onChange={(e) => setSettings({ ...settings, roundup_threshold: parseFloat(e.target.value) || 5 })}
              className={`w-24 p-2 rounded border ${
                darkMode
                  ? 'bg-gray-700 border-gray-600 text-white'
                  : 'bg-white border-gray-300 text-gray-800'
              }`}
            />
          </div>
          <p className={`text-xs mt-2 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
            Invest when round-ups reach this amount
          </p>
        </div>
      )}
    </div>
  );

  // Step 4: Choose investment target
  const renderStep4 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-center">Where to Invest</h2>
      <p className={`text-center ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
        Choose where your round-ups should be invested.
      </p>

      <div className="space-y-4 max-w-md mx-auto">
        {/* Recommended ETF option */}
        <button
          onClick={() => setSettings({ ...settings, micro_invest_target_type: 'recommended_etf' })}
          className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
            settings.micro_invest_target_type === 'recommended_etf'
              ? selectedClass
              : `${cardClass} hover:border-blue-400`
          }`}
        >
          <span className="font-medium">Recommended ETF</span>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Invest in a diversified ETF
          </p>
        </button>

        {settings.micro_invest_target_type === 'recommended_etf' && (
          <div className="grid grid-cols-2 gap-2 pl-4">
            {RECOMMENDED_ETFS.map((etf) => (
              <button
                key={etf.symbol}
                onClick={() => setSelectedETF(etf.symbol)}
                className={`p-3 rounded-lg border text-left text-sm ${
                  selectedETF === etf.symbol
                    ? 'border-green-500 bg-green-900/30'
                    : darkMode
                      ? 'border-gray-700 bg-gray-800'
                      : 'border-gray-200 bg-white'
                }`}
              >
                <span className="font-bold">{etf.symbol}</span>
                <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {etf.description}
                </p>
              </button>
            ))}
          </div>
        )}

        {/* Portfolio option */}
        <button
          onClick={() => setSettings({ ...settings, micro_invest_target_type: 'default_portfolio' })}
          className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
            settings.micro_invest_target_type === 'default_portfolio'
              ? selectedClass
              : `${cardClass} hover:border-blue-400`
          }`}
        >
          <span className="font-medium">My Portfolio</span>
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Add to your existing portfolio allocation
          </p>
        </button>
      </div>
    </div>
  );

  // Step 5: Review and confirm
  const renderStep5 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-center">Review Your Settings</h2>
      <p className={`text-center ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
        Confirm your round-up investment settings.
      </p>

      <div className={`p-6 rounded-lg ${cardClass} max-w-md mx-auto space-y-4`}>
        <div className="flex justify-between">
          <span className={darkMode ? 'text-gray-400' : 'text-gray-500'}>Status</span>
          <span className={settings.roundup_enabled ? 'text-green-500 font-medium' : 'text-red-500'}>
            {settings.roundup_enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>

        <div className="flex justify-between">
          <span className={darkMode ? 'text-gray-400' : 'text-gray-500'}>Multiplier</span>
          <span className="font-medium">{settings.roundup_multiplier}x</span>
        </div>

        <div className="flex justify-between">
          <span className={darkMode ? 'text-gray-400' : 'text-gray-500'}>Frequency</span>
          <span className="font-medium capitalize">{settings.roundup_frequency}</span>
        </div>

        {settings.roundup_frequency === 'threshold' && (
          <div className="flex justify-between">
            <span className={darkMode ? 'text-gray-400' : 'text-gray-500'}>Threshold</span>
            <span className="font-medium">{formatCurrency(settings.roundup_threshold)}</span>
          </div>
        )}

        <div className="flex justify-between">
          <span className={darkMode ? 'text-gray-400' : 'text-gray-500'}>Invest In</span>
          <span className="font-medium">
            {settings.micro_invest_target_type === 'recommended_etf'
              ? selectedETF
              : settings.micro_invest_target_type === 'default_portfolio'
                ? 'My Portfolio'
                : settings.micro_invest_target_type}
          </span>
        </div>

        <div className="pt-4 border-t border-gray-700">
          <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Weekly savings estimate (based on 10 purchases/week):
          </p>
          <p className="text-2xl font-bold text-green-500">
            ~{formatCurrency(5 * settings.roundup_multiplier)}/week
          </p>
        </div>
      </div>

      {/* Notification preferences */}
      <div className={`p-4 rounded-lg ${cardClass} max-w-md mx-auto`}>
        <h4 className="font-medium mb-3">Notifications</h4>
        <label className="flex items-center justify-between mb-2">
          <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Notify on round-up collection
          </span>
          <input
            type="checkbox"
            checked={settings.notify_on_roundup}
            onChange={(e) => setSettings({ ...settings, notify_on_roundup: e.target.checked })}
            className="w-5 h-5"
          />
        </label>
        <label className="flex items-center justify-between">
          <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            Notify on investment
          </span>
          <input
            type="checkbox"
            checked={settings.notify_on_investment}
            onChange={(e) => setSettings({ ...settings, notify_on_investment: e.target.checked })}
            className="w-5 h-5"
          />
        </label>
      </div>
    </div>
  );

  // Render current step
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

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${containerClass}`}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-4 md:p-8 ${containerClass}`}>
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold">Round-Up Setup</h1>
          <button
            onClick={onCancel || (() => navigate(-1))}
            className={`p-2 rounded-full ${darkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-100'}`}
          >
            ✕
          </button>
        </div>

        {/* Progress */}
        {renderProgress()}

        {/* Current Step */}
        <div className="mb-8">
          {renderCurrentStep()}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between max-w-md mx-auto">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              currentStep === 1
                ? 'opacity-50 cursor-not-allowed'
                : buttonSecondaryClass
            }`}
          >
            Back
          </button>

          {currentStep < totalSteps ? (
            <button
              onClick={handleNext}
              disabled={!settings.roundup_enabled && currentStep === 1}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${buttonPrimaryClass}`}
            >
              Continue
            </button>
          ) : (
            <button
              onClick={handleSave}
              disabled={saving}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${buttonPrimaryClass} flex items-center`}
            >
              {saving ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">Saving...</span>
                </>
              ) : (
                'Enable Round-Ups'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default RoundupSetupWizard;
