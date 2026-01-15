import React, { useState } from 'react';
import {
  useSuccessionPlanningMutation,
  WealthAdvisoryResponse,
  ProfessionalRole,
} from '../../services/wealthAdvisoryApi';

interface SuccessionFormData {
  businessType: string;
  estimatedValue: number;
  ownerAge: number;
  familySuccessors: number;
  keyEmployees: number;
  timelineYears: number;
  concerns: string[];
  currentStructure: string;
}

const BUSINESS_TYPES = [
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'retail', label: 'Retail/Consumer' },
  { value: 'professional_services', label: 'Professional Services' },
  { value: 'technology', label: 'Technology' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'financial_services', label: 'Financial Services' },
  { value: 'construction', label: 'Construction' },
  { value: 'agriculture', label: 'Agriculture' },
  { value: 'other', label: 'Other' },
];

const COMMON_CONCERNS = [
  { id: 'tax_efficiency', label: 'Tax Efficiency', icon: '💰' },
  { id: 'family_harmony', label: 'Family Harmony', icon: '👨‍👩‍👧‍👦' },
  { id: 'employee_retention', label: 'Key Employee Retention', icon: '👥' },
  { id: 'business_continuity', label: 'Business Continuity', icon: '🔄' },
  { id: 'fair_distribution', label: 'Fair Distribution to Heirs', icon: '⚖️' },
  { id: 'minority_protection', label: 'Minority Shareholder Protection', icon: '🛡️' },
  { id: 'liquidity', label: 'Liquidity for Estate Taxes', icon: '💧' },
  { id: 'control_transition', label: 'Gradual Control Transition', icon: '📊' },
];

const STRUCTURE_OPTIONS = [
  { value: 'sole_proprietorship', label: 'Sole Proprietorship' },
  { value: 'partnership', label: 'Partnership' },
  { value: 'llc', label: 'LLC' },
  { value: 's_corp', label: 'S Corporation' },
  { value: 'c_corp', label: 'C Corporation' },
  { value: 'family_limited_partnership', label: 'Family Limited Partnership' },
  { value: 'holding_company', label: 'Holding Company Structure' },
];

const DREAM_TEAM = [
  {
    role: 'CFP',
    title: 'Certified Financial Planner',
    responsibility: 'Quarterback - defines personal financial objectives',
    icon: '🎯',
  },
  {
    role: 'M&A Attorney',
    title: 'M&A Attorney',
    responsibility: 'Transaction structure, purchase agreements, legal risks',
    icon: '⚖️',
  },
  {
    role: 'CPA',
    title: 'Certified Public Accountant',
    responsibility: 'Tax-efficient structuring, due diligence',
    icon: '🧮',
  },
  {
    role: 'Valuation Expert',
    title: 'Business Valuation Expert',
    responsibility: 'Objective pricing, tax challenge defense',
    icon: '💹',
  },
  {
    role: 'Estate Attorney',
    title: 'Estate Planning Attorney',
    responsibility: 'Plan updates, seller notes, trust adjustments',
    icon: '📜',
  },
  {
    role: 'Wealth Manager',
    title: 'Wealth Manager',
    responsibility: 'Post-transaction investment, tax optimization',
    icon: '💎',
  },
];

interface SuccessionPlannerProps {
  onTeamRecommendation?: (professionals: ProfessionalRole[]) => void;
}

const SuccessionPlanner: React.FC<SuccessionPlannerProps> = ({
  onTeamRecommendation,
}) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<SuccessionFormData>({
    businessType: '',
    estimatedValue: 0,
    ownerAge: 55,
    familySuccessors: 0,
    keyEmployees: 0,
    timelineYears: 5,
    concerns: [],
    currentStructure: '',
  });
  const [result, setResult] = useState<WealthAdvisoryResponse | null>(null);

  const [submitPlan, { isLoading }] = useSuccessionPlanningMutation();

  const handleInputChange = (field: keyof SuccessionFormData, value: string | number | string[]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleConcern = (concernId: string) => {
    setFormData((prev) => ({
      ...prev,
      concerns: prev.concerns.includes(concernId)
        ? prev.concerns.filter((c) => c !== concernId)
        : [...prev.concerns, concernId],
    }));
  };

  const handleSubmit = async () => {
    try {
      const response = await submitPlan({
        business_type: formData.businessType,
        estimated_value: formData.estimatedValue,
        owner_age: formData.ownerAge,
        family_successors: formData.familySuccessors,
        key_employees: formData.keyEmployees,
        timeline_years: formData.timelineYears,
      }).unwrap();

      setResult(response);
      onTeamRecommendation?.(response.recommended_professionals);
      setStep(4);
    } catch (error) {
      console.error('Failed to generate succession plan:', error);
    }
  };

  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value}`;
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Business Type
        </label>
        <select
          value={formData.businessType}
          onChange={(e) => handleInputChange('businessType', e.target.value)}
          className="w-full bg-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="">Select business type...</option>
          {BUSINESS_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Current Business Structure
        </label>
        <select
          value={formData.currentStructure}
          onChange={(e) => handleInputChange('currentStructure', e.target.value)}
          className="w-full bg-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="">Select structure...</option>
          {STRUCTURE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Estimated Business Value: {formatCurrency(formData.estimatedValue)}
        </label>
        <input
          type="range"
          min={100000}
          max={100000000}
          step={100000}
          value={formData.estimatedValue}
          onChange={(e) => handleInputChange('estimatedValue', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>$100K</span>
          <span>$100M</span>
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Current Owner Age: {formData.ownerAge} years
        </label>
        <input
          type="range"
          min={35}
          max={85}
          value={formData.ownerAge}
          onChange={(e) => handleInputChange('ownerAge', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>35</span>
          <span>85</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Potential Family Successors: {formData.familySuccessors}
        </label>
        <input
          type="range"
          min={0}
          max={10}
          value={formData.familySuccessors}
          onChange={(e) => handleInputChange('familySuccessors', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0 (External sale)</span>
          <span>10+</span>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Key Employees to Retain: {formData.keyEmployees}
        </label>
        <input
          type="range"
          min={0}
          max={50}
          value={formData.keyEmployees}
          onChange={(e) => handleInputChange('keyEmployees', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Target Timeline: {formData.timelineYears} years
        </label>
        <input
          type="range"
          min={1}
          max={20}
          value={formData.timelineYears}
          onChange={(e) => handleInputChange('timelineYears', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>1 year (Urgent)</span>
          <span>20 years (Long-term)</span>
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-4">
          Primary Concerns (Select all that apply)
        </label>
        <div className="grid grid-cols-2 gap-3">
          {COMMON_CONCERNS.map((concern) => (
            <button
              key={concern.id}
              onClick={() => toggleConcern(concern.id)}
              className={`p-4 rounded-lg text-left transition-colors ${
                formData.concerns.includes(concern.id)
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <span className="text-2xl mr-2">{concern.icon}</span>
              <span className="text-sm">{concern.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Dream Team Preview */}
      <div className="mt-6 p-4 bg-gray-900 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-3">
          The "Dream Team" Approach
        </h3>
        <p className="text-sm text-gray-400 mb-4">
          Business succession planning requires coordinated expertise. Here's the recommended team:
        </p>
        <div className="grid grid-cols-2 gap-2">
          {DREAM_TEAM.map((member) => (
            <div
              key={member.role}
              className="p-3 bg-gray-800 rounded-lg"
            >
              <div className="flex items-center mb-1">
                <span className="text-xl mr-2">{member.icon}</span>
                <span className="font-medium text-white text-sm">
                  {member.role}
                </span>
              </div>
              <p className="text-xs text-gray-400">
                {member.responsibility}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderResult = () => (
    <div className="space-y-6">
      {result && (
        <>
          {/* Summary Card */}
          <div className="p-4 bg-purple-900/30 rounded-lg border border-purple-700">
            <h3 className="text-lg font-bold text-white mb-2">
              Succession Plan Summary
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Business Value:</span>
                <span className="ml-2 text-white font-medium">
                  {formatCurrency(formData.estimatedValue)}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Timeline:</span>
                <span className="ml-2 text-white font-medium">
                  {formData.timelineYears} years
                </span>
              </div>
              <div>
                <span className="text-gray-400">Family Successors:</span>
                <span className="ml-2 text-white font-medium">
                  {formData.familySuccessors}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Confidence:</span>
                <span className="ml-2 text-white font-medium">
                  {Math.round((result.confidence || 0) * 100)}%
                </span>
              </div>
            </div>
          </div>

          {/* AI Response */}
          <div className="p-4 bg-gray-700 rounded-lg">
            <h4 className="font-semibold text-white mb-2">Analysis & Recommendations</h4>
            <div className="text-gray-300 whitespace-pre-wrap">
              {result.response}
            </div>
          </div>

          {/* Recommended Team */}
          {result.recommended_professionals && result.recommended_professionals.length > 0 && (
            <div className="p-4 bg-gray-700 rounded-lg">
              <h4 className="font-semibold text-white mb-3">
                Recommended Professional Team
              </h4>
              <div className="space-y-2">
                {result.recommended_professionals.map((prof, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-gray-800 rounded-lg flex items-center justify-between"
                  >
                    <div>
                      <span className="font-medium text-white">
                        {prof.title}
                      </span>
                      {prof.credentials.length > 0 && (
                        <span className="ml-2 text-purple-400 text-sm">
                          ({prof.credentials.join(', ')})
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400 capitalize">
                      {prof.decision_authority.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Next Steps */}
          {result.next_steps && result.next_steps.length > 0 && (
            <div className="p-4 bg-gray-700 rounded-lg">
              <h4 className="font-semibold text-white mb-2">Next Steps</h4>
              <ol className="list-decimal list-inside text-gray-300 space-y-2">
                {result.next_steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Compliance Flags */}
          {result.compliance_flags && result.compliance_flags.length > 0 && (
            <div className="p-4 bg-yellow-900/30 rounded-lg border border-yellow-700">
              <h4 className="font-semibold text-yellow-400 mb-2">
                Compliance Considerations
              </h4>
              <ul className="list-disc list-inside text-yellow-200 text-sm space-y-1">
                {result.compliance_flags.map((flag, idx) => (
                  <li key={idx}>{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );

  return (
    <div className="bg-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center mb-4">
          <span className="text-2xl mr-3">🔄</span>
          <div>
            <h2 className="text-lg font-bold text-white">
              Business Succession Planner
            </h2>
            <p className="text-sm text-gray-400">
              Plan your business transition with the "Dream Team" approach
            </p>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-between">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= s
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-400'
                }`}
              >
                {s === 4 ? '✓' : s}
              </div>
              {s < 4 && (
                <div
                  className={`w-16 h-1 mx-2 ${
                    step > s ? 'bg-purple-600' : 'bg-gray-700'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>Business Info</span>
          <span>People</span>
          <span>Concerns</span>
          <span>Results</span>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}
        {step === 4 && renderResult()}
      </div>

      {/* Navigation */}
      <div className="p-4 bg-gray-900 border-t border-gray-700 flex justify-between">
        <button
          onClick={() => setStep((s) => Math.max(1, s - 1))}
          disabled={step === 1}
          className="px-6 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 text-white rounded-lg transition-colors"
        >
          Back
        </button>

        {step < 3 && (
          <button
            onClick={() => setStep((s) => s + 1)}
            disabled={step === 1 && (!formData.businessType || formData.estimatedValue === 0)}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg transition-colors"
          >
            Continue
          </button>
        )}

        {step === 3 && (
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white rounded-lg transition-colors flex items-center"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Analyzing...
              </>
            ) : (
              'Generate Plan'
            )}
          </button>
        )}

        {step === 4 && (
          <button
            onClick={() => {
              setStep(1);
              setResult(null);
              setFormData({
                businessType: '',
                estimatedValue: 0,
                ownerAge: 55,
                familySuccessors: 0,
                keyEmployees: 0,
                timelineYears: 5,
                concerns: [],
                currentStructure: '',
              });
            }}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Start New Plan
          </button>
        )}
      </div>
    </div>
  );
};

export default SuccessionPlanner;
