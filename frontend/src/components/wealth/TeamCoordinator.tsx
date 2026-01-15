import React, { useState } from 'react';
import {
  useTeamCoordinationMutation,
  TeamRecommendation,
  ProfessionalRole,
} from '../../services/wealthAdvisoryApi';

type ComplexityLevel = 'basic' | 'moderate' | 'complex' | 'highly_complex';

interface TeamFormData {
  planningType: string;
  complexityLevel: ComplexityLevel;
  estimatedValue: number;
  specificNeeds: string[];
}

const PLANNING_TYPES = [
  { value: 'estate_planning', label: 'Estate Planning', icon: '🏛️', description: 'Wills, trusts, asset protection' },
  { value: 'business_succession', label: 'Business Succession', icon: '🔄', description: 'Ownership transition planning' },
  { value: 'investment_management', label: 'Investment Management', icon: '📈', description: 'Portfolio and asset allocation' },
  { value: 'tax_planning', label: 'Tax Planning', icon: '📊', description: 'Tax optimization strategies' },
  { value: 'retirement_planning', label: 'Retirement Planning', icon: '🏖️', description: 'Retirement income planning' },
  { value: 'philanthropic_planning', label: 'Philanthropic Planning', icon: '❤️', description: 'Charitable giving strategies' },
  { value: 'family_governance', label: 'Family Governance', icon: '👨‍👩‍👧‍👦', description: 'Family office structure' },
  { value: 'risk_management', label: 'Risk Management', icon: '🛡️', description: 'Insurance and protection' },
];

const COMPLEXITY_LEVELS: { value: ComplexityLevel; label: string; description: string; color: string }[] = [
  { value: 'basic', label: 'Basic', description: 'Single domain, straightforward needs', color: 'bg-green-600' },
  { value: 'moderate', label: 'Moderate', description: 'Multiple domains, some coordination', color: 'bg-yellow-600' },
  { value: 'complex', label: 'Complex', description: 'Multiple entities, cross-border considerations', color: 'bg-orange-600' },
  { value: 'highly_complex', label: 'Highly Complex', description: 'Multi-generational, international, significant assets', color: 'bg-red-600' },
];

const SPECIFIC_NEEDS = [
  { id: 'multi_state', label: 'Multi-State Planning', category: 'Geographic' },
  { id: 'international', label: 'International/Cross-Border', category: 'Geographic' },
  { id: 'business_owner', label: 'Business Owner', category: 'Asset Type' },
  { id: 'real_estate', label: 'Significant Real Estate', category: 'Asset Type' },
  { id: 'alternative_investments', label: 'Alternative Investments', category: 'Asset Type' },
  { id: 'closely_held_stock', label: 'Closely Held Stock', category: 'Asset Type' },
  { id: 'special_needs', label: 'Special Needs Beneficiary', category: 'Family' },
  { id: 'blended_family', label: 'Blended Family', category: 'Family' },
  { id: 'minor_children', label: 'Minor Children', category: 'Family' },
  { id: 'charitable_intent', label: 'Charitable Intent', category: 'Goals' },
  { id: 'privacy_concerns', label: 'Privacy/Asset Protection', category: 'Goals' },
  { id: 'litigation_risk', label: 'Litigation Risk', category: 'Risk' },
];

const COORDINATION_MODELS = {
  'CFP as Quarterback': {
    description: 'CFP leads coordination with specialized professionals',
    bestFor: 'Most comprehensive planning needs',
    meetingCadence: 'Quarterly team meetings, monthly CFP check-ins',
  },
  'Attorney-Led': {
    description: 'Estate/Trust attorney leads for legal-heavy matters',
    bestFor: 'Complex trust structures, litigation, family disputes',
    meetingCadence: 'As-needed basis, milestone-driven',
  },
  'CPA-Led': {
    description: 'CPA leads for tax-centric planning',
    bestFor: 'Business owners, complex tax situations',
    meetingCadence: 'Quarterly with tax deadline peaks',
  },
  'Investment Committee': {
    description: 'Formal committee structure with charter',
    bestFor: 'Large portfolios, family offices, institutional approach',
    meetingCadence: 'Monthly committee, weekly investment review',
  },
};

interface TeamCoordinatorProps {
  onTeamBuilt?: (team: TeamRecommendation) => void;
}

const TeamCoordinator: React.FC<TeamCoordinatorProps> = ({ onTeamBuilt }) => {
  const [formData, setFormData] = useState<TeamFormData>({
    planningType: '',
    complexityLevel: 'moderate',
    estimatedValue: 500000,
    specificNeeds: [],
  });
  const [recommendation, setRecommendation] = useState<TeamRecommendation | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  const [getRecommendation, { isLoading }] = useTeamCoordinationMutation();

  const handlePlanningTypeSelect = (type: string) => {
    setFormData((prev) => ({ ...prev, planningType: type }));
  };

  const handleComplexitySelect = (level: ComplexityLevel) => {
    setFormData((prev) => ({ ...prev, complexityLevel: level }));
  };

  const toggleNeed = (needId: string) => {
    setFormData((prev) => ({
      ...prev,
      specificNeeds: prev.specificNeeds.includes(needId)
        ? prev.specificNeeds.filter((n) => n !== needId)
        : [...prev.specificNeeds, needId],
    }));
  };

  const handleSubmit = async () => {
    try {
      const result = await getRecommendation({
        planning_type: formData.planningType,
        complexity_level: formData.complexityLevel,
        estimated_value: formData.estimatedValue,
        specific_needs: formData.specificNeeds,
      }).unwrap();

      setRecommendation(result);
      onTeamBuilt?.(result);
    } catch (error) {
      console.error('Failed to get team recommendation:', error);
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

  const renderRoleCard = (role: ProfessionalRole, isPrimary: boolean = false) => (
    <div
      className={`p-4 rounded-lg ${
        isPrimary ? 'bg-purple-900/50 border border-purple-600' : 'bg-gray-700'
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h4 className={`font-semibold ${isPrimary ? 'text-purple-200' : 'text-white'}`}>
            {role.title}
            {isPrimary && (
              <span className="ml-2 px-2 py-0.5 bg-purple-600 text-white text-xs rounded-full">
                Lead
              </span>
            )}
          </h4>
          {role.credentials.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {role.credentials.map((cred, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-gray-800 text-gray-300 text-xs rounded"
                >
                  {cred}
                </span>
              ))}
            </div>
          )}
        </div>
        <span className="text-xs text-gray-400 capitalize">
          {role.decision_authority.replace('_', ' ')}
        </span>
      </div>
      {role.key_responsibilities.length > 0 && (
        <ul className="mt-2 text-sm text-gray-400 space-y-1">
          {role.key_responsibilities.slice(0, 3).map((resp, idx) => (
            <li key={idx} className="flex items-start">
              <span className="mr-2">•</span>
              <span>{resp}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  return (
    <div className="bg-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center">
          <span className="text-2xl mr-3">🤝</span>
          <div>
            <h2 className="text-lg font-bold text-white">
              Advisory Team Coordinator
            </h2>
            <p className="text-sm text-gray-400">
              Build your optimal professional advisory team
            </p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {!recommendation ? (
          <div className="space-y-8">
            {/* Planning Type Selection */}
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                1. Select Planning Type
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {PLANNING_TYPES.map((type) => (
                  <button
                    key={type.value}
                    onClick={() => handlePlanningTypeSelect(type.value)}
                    className={`p-4 rounded-lg text-left transition-colors ${
                      formData.planningType === type.value
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    <span className="text-2xl block mb-2">{type.icon}</span>
                    <span className="font-medium block">{type.label}</span>
                    <span className="text-xs opacity-75">{type.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Complexity Level */}
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                2. Complexity Level
              </h3>
              <div className="grid grid-cols-4 gap-3">
                {COMPLEXITY_LEVELS.map((level) => (
                  <button
                    key={level.value}
                    onClick={() => handleComplexitySelect(level.value)}
                    className={`p-4 rounded-lg text-center transition-colors ${
                      formData.complexityLevel === level.value
                        ? `${level.color} text-white`
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    <span className="font-medium block">{level.label}</span>
                    <span className="text-xs opacity-75 block mt-1">
                      {level.description}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Estimated Value */}
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                3. Estimated Asset Value: {formatCurrency(formData.estimatedValue)}
              </h3>
              <input
                type="range"
                min={10000}
                max={50000000}
                step={10000}
                value={formData.estimatedValue}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    estimatedValue: parseInt(e.target.value),
                  }))
                }
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>$10K</span>
                <span>$50M</span>
              </div>
            </div>

            {/* Specific Needs */}
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                4. Specific Needs (Optional)
              </h3>
              <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
                {SPECIFIC_NEEDS.map((need) => (
                  <button
                    key={need.id}
                    onClick={() => toggleNeed(need.id)}
                    className={`p-3 rounded-lg text-sm transition-colors ${
                      formData.specificNeeds.includes(need.id)
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {need.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Coordination Models Preview */}
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                5. Coordination Model
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(COORDINATION_MODELS).map(([name, model]) => (
                  <button
                    key={name}
                    onClick={() => setSelectedModel(name)}
                    className={`p-4 rounded-lg text-left transition-colors ${
                      selectedModel === name
                        ? 'bg-purple-900/50 border border-purple-600'
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    <h4 className="font-medium text-white">{name}</h4>
                    <p className="text-xs text-gray-400 mt-1">{model.description}</p>
                    <p className="text-xs text-purple-400 mt-2">
                      Best for: {model.bestFor}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={!formData.planningType || isLoading}
              className="w-full py-4 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold rounded-lg transition-colors flex items-center justify-center"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3" />
                  Building Your Team...
                </>
              ) : (
                'Build Advisory Team'
              )}
            </button>
          </div>
        ) : (
          /* Results View */
          <div className="space-y-6">
            {/* Team Summary */}
            <div className="p-4 bg-purple-900/30 rounded-lg border border-purple-700">
              <h3 className="text-lg font-bold text-white mb-2">
                Your Advisory Team
              </h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Planning Type:</span>
                  <span className="ml-2 text-white capitalize">
                    {formData.planningType.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Complexity:</span>
                  <span className="ml-2 text-white capitalize">
                    {formData.complexityLevel.replace('_', ' ')}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Value:</span>
                  <span className="ml-2 text-white">
                    {formatCurrency(formData.estimatedValue)}
                  </span>
                </div>
              </div>
            </div>

            {/* Primary Advisor */}
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-2">
                Primary Advisor (Team Lead)
              </h4>
              {renderRoleCard(recommendation.primary_advisor, true)}
            </div>

            {/* Supporting Team */}
            {recommendation.supporting_team.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-400 mb-2">
                  Supporting Team ({recommendation.supporting_team.length} professionals)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {recommendation.supporting_team.map((role, idx) => (
                    <div key={idx}>{renderRoleCard(role)}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Coordination Structure */}
            <div className="p-4 bg-gray-700 rounded-lg">
              <h4 className="font-semibold text-white mb-2">
                Coordination Structure
              </h4>
              <p className="text-gray-300">{recommendation.coordination_structure}</p>
              <div className="mt-3 flex items-center text-sm">
                <span className="text-gray-400">Meeting Cadence:</span>
                <span className="ml-2 text-purple-400">
                  {recommendation.meeting_cadence}
                </span>
              </div>
            </div>

            {/* Fee Estimate */}
            <div className="p-4 bg-gray-700 rounded-lg">
              <h4 className="font-semibold text-white mb-2">
                Estimated Annual Fee Range
              </h4>
              <p className="text-2xl text-purple-400 font-bold">
                {recommendation.estimated_fee_range}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Actual fees vary based on advisor and scope of engagement
              </p>
            </div>

            {/* Reset Button */}
            <button
              onClick={() => {
                setRecommendation(null);
                setSelectedModel(null);
              }}
              className="w-full py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Build Different Team
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamCoordinator;
