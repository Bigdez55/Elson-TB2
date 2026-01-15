import React, { useState } from 'react';
import {
  useGetRoleInfoQuery,
  useGetCertificationInfoQuery,
  DecisionAuthority,
} from '../../services/wealthAdvisoryApi';

// Role categories and their roles
const ROLE_CATEGORIES = {
  'Executive Leadership': [
    { id: 'ceo', title: 'Chief Executive Officer', icon: '👔' },
    { id: 'cio', title: 'Chief Investment Officer', icon: '📊' },
    { id: 'cfo', title: 'Chief Financial Officer', icon: '💰' },
    { id: 'coo', title: 'Chief Operating Officer', icon: '⚙️' },
    { id: 'cro', title: 'Chief Risk Officer', icon: '🛡️' },
    { id: 'cto', title: 'Chief Technology Officer', icon: '💻' },
    { id: 'cco', title: 'Chief Compliance Officer', icon: '✅' },
  ],
  'Legal Specialists': [
    { id: 'estate_planning_attorney', title: 'Estate Planning Attorney', icon: '⚖️' },
    { id: 'probate_attorney', title: 'Probate Attorney', icon: '📜' },
    { id: 'trust_admin_attorney', title: 'Trust Administration Attorney', icon: '🏛️' },
    { id: 'international_tax_attorney', title: 'International Tax Attorney', icon: '🌍' },
    { id: 'ma_attorney', title: 'M&A Attorney', icon: '🤝' },
    { id: 'securities_counsel', title: 'Securities Counsel', icon: '📋' },
  ],
  'Financial Advisors': [
    { id: 'cfp', title: 'Certified Financial Planner (CFP)', icon: '📈' },
    { id: 'cfa', title: 'Chartered Financial Analyst (CFA)', icon: '📉' },
    { id: 'cpa', title: 'Certified Public Accountant (CPA)', icon: '🧮' },
    { id: 'cpwa', title: 'Certified Private Wealth Advisor (CPWA)', icon: '💎' },
    { id: 'chfc', title: 'Chartered Financial Consultant (ChFC)', icon: '🎯' },
    { id: 'cima', title: 'Certified Investment Management Analyst (CIMA)', icon: '📊' },
  ],
  'Fiduciary Roles': [
    { id: 'trustee', title: 'Trustee', icon: '🔐' },
    { id: 'trust_protector', title: 'Trust Protector', icon: '🛡️' },
    { id: 'investment_adviser', title: 'Investment Adviser', icon: '📈' },
    { id: 'special_fiduciary', title: 'Special Fiduciary', icon: '⚖️' },
  ],
  'Specialized Advisors': [
    { id: 'philanthropic_advisor', title: 'Philanthropic Advisor', icon: '❤️' },
    { id: 'business_valuator', title: 'Business Valuation Expert', icon: '💹' },
    { id: 'insurance_specialist', title: 'Insurance/Risk Advisor', icon: '🏥' },
    { id: 'family_governance', title: 'Family Governance Officer', icon: '👨‍👩‍👧‍👦' },
  ],
  'Operational Roles': [
    { id: 'relationship_manager', title: 'Relationship Manager', icon: '🤝' },
    { id: 'tax_manager', title: 'Tax Manager', icon: '📋' },
    { id: 'real_estate_manager', title: 'Real Estate Manager', icon: '🏠' },
    { id: 'portfolio_manager', title: 'Portfolio Manager', icon: '💼' },
    { id: 'investment_analyst', title: 'Investment Analyst', icon: '🔍' },
  ],
};

const CERTIFICATIONS = [
  { id: 'cfp', name: 'CFP - Certified Financial Planner', studyHours: '300+' },
  { id: 'cfa', name: 'CFA - Chartered Financial Analyst', studyHours: '2000+' },
  { id: 'cpa', name: 'CPA - Certified Public Accountant', studyHours: '200-240' },
  { id: 'cpwa', name: 'CPWA - Certified Private Wealth Advisor', studyHours: 'Advanced' },
  { id: 'chfc', name: 'ChFC - Chartered Financial Consultant', studyHours: '200+' },
  { id: 'cima', name: 'CIMA - Certified Investment Management Analyst', studyHours: '500+' },
  { id: 'cva', name: 'CVA - Certified Valuation Analyst', studyHours: '200+' },
  { id: 'asa', name: 'ASA - Accredited Senior Appraiser', studyHours: '300+' },
];

const AUTHORITY_COLORS: Record<DecisionAuthority, { bg: string; text: string; label: string }> = {
  binding: { bg: 'bg-red-900/50', text: 'text-red-300', label: 'Binding Authority' },
  senior_advisory: { bg: 'bg-orange-900/50', text: 'text-orange-300', label: 'Senior Advisory' },
  advisory: { bg: 'bg-blue-900/50', text: 'text-blue-300', label: 'Advisory' },
  support_role: { bg: 'bg-gray-700', text: 'text-gray-300', label: 'Support Role' },
};

interface ProfessionalRolesGuideProps {
  onRoleSelect?: (roleId: string) => void;
}

const ProfessionalRolesGuide: React.FC<ProfessionalRolesGuideProps> = ({
  onRoleSelect,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('Financial Advisors');
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [selectedCertification, setSelectedCertification] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'roles' | 'certifications'>('roles');

  const { data: roleData, isLoading: roleLoading } = useGetRoleInfoQuery(selectedRole || '', {
    skip: !selectedRole,
  });

  const { data: certData, isLoading: certLoading } = useGetCertificationInfoQuery(
    selectedCertification || '',
    { skip: !selectedCertification }
  );

  const handleRoleClick = (roleId: string) => {
    setSelectedRole(roleId);
    setSelectedCertification(null);
    onRoleSelect?.(roleId);
  };

  const handleCertificationClick = (certId: string) => {
    setSelectedCertification(certId);
    setSelectedRole(null);
  };

  return (
    <div className="bg-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">👥</span>
            <div>
              <h2 className="text-lg font-bold text-white">
                Professional Roles Guide
              </h2>
              <p className="text-sm text-gray-400">
                70+ wealth management professionals
              </p>
            </div>
          </div>
          <div className="flex bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('roles')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'roles'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Roles
            </button>
            <button
              onClick={() => setViewMode('certifications')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'certifications'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Certifications
            </button>
          </div>
        </div>

        {/* Decision Authority Legend */}
        <div className="flex flex-wrap gap-2">
          {Object.entries(AUTHORITY_COLORS).map(([key, value]) => (
            <div
              key={key}
              className={`px-2 py-1 rounded text-xs ${value.bg} ${value.text}`}
            >
              {value.label}
            </div>
          ))}
        </div>
      </div>

      <div className="flex h-[500px]">
        {/* Left sidebar - Categories/Certifications */}
        <div className="w-1/3 border-r border-gray-700 overflow-y-auto">
          {viewMode === 'roles' ? (
            <div className="p-2">
              {Object.entries(ROLE_CATEGORIES).map(([category, roles]) => (
                <div key={category} className="mb-2">
                  <button
                    onClick={() => setSelectedCategory(category)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedCategory === category
                        ? 'bg-purple-900/50 text-purple-200'
                        : 'hover:bg-gray-700 text-gray-300'
                    }`}
                  >
                    <div className="font-medium">{category}</div>
                    <div className="text-xs text-gray-500">
                      {roles.length} roles
                    </div>
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-2">
              {CERTIFICATIONS.map((cert) => (
                <button
                  key={cert.id}
                  onClick={() => handleCertificationClick(cert.id)}
                  className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                    selectedCertification === cert.id
                      ? 'bg-purple-900/50 text-purple-200'
                      : 'hover:bg-gray-700 text-gray-300'
                  }`}
                >
                  <div className="font-medium">{cert.name}</div>
                  <div className="text-xs text-gray-500">
                    Study: {cert.studyHours} hours
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Middle - Role/Cert list */}
        <div className="w-1/3 border-r border-gray-700 overflow-y-auto p-2">
          {viewMode === 'roles' && selectedCategory && (
            <div>
              <h3 className="text-sm font-semibold text-gray-400 px-2 mb-2">
                {selectedCategory}
              </h3>
              {ROLE_CATEGORIES[selectedCategory as keyof typeof ROLE_CATEGORIES]?.map((role) => (
                <button
                  key={role.id}
                  onClick={() => handleRoleClick(role.id)}
                  className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                    selectedRole === role.id
                      ? 'bg-purple-600 text-white'
                      : 'hover:bg-gray-700 text-gray-300'
                  }`}
                >
                  <div className="flex items-center">
                    <span className="text-xl mr-2">{role.icon}</span>
                    <span>{role.title}</span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {viewMode === 'certifications' && !selectedCertification && (
            <div className="p-4 text-center text-gray-500">
              Select a certification to view details
            </div>
          )}
        </div>

        {/* Right - Details panel */}
        <div className="w-1/3 overflow-y-auto p-4">
          {viewMode === 'roles' && selectedRole && (
            <>
              {roleLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
                </div>
              ) : roleData ? (
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">
                    {roleData.title}
                  </h3>

                  {/* Credentials */}
                  {roleData.credentials && roleData.credentials.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Required Credentials
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {roleData.credentials.map((cred, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-purple-900/50 text-purple-200 rounded text-xs"
                          >
                            {cred}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Study Hours */}
                  {roleData.study_hours && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Study Hours
                      </h4>
                      <p className="text-gray-300">{roleData.study_hours}</p>
                    </div>
                  )}

                  {/* Key Responsibilities */}
                  {roleData.key_responsibilities && roleData.key_responsibilities.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Key Responsibilities
                      </h4>
                      <ul className="list-disc list-inside text-gray-300 text-sm space-y-1">
                        {roleData.key_responsibilities.map((resp, idx) => (
                          <li key={idx}>{resp}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Typical Clients */}
                  {roleData.typical_clients && roleData.typical_clients.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Typical Clients
                      </h4>
                      <ul className="list-disc list-inside text-gray-300 text-sm space-y-1">
                        {roleData.typical_clients.map((client, idx) => (
                          <li key={idx}>{client}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Career Path */}
                  {roleData.career_path && roleData.career_path.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Career Path
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {roleData.career_path.map((step, idx) => (
                          <span key={idx} className="flex items-center text-sm text-gray-300">
                            {step}
                            {idx < roleData.career_path!.length - 1 && (
                              <span className="mx-2 text-gray-500">→</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  Select a role to view details
                </div>
              )}
            </>
          )}

          {viewMode === 'certifications' && selectedCertification && (
            <>
              {certLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
                </div>
              ) : certData ? (
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">
                    {certData.acronym}
                  </h3>
                  <p className="text-gray-400 mb-4">{certData.name}</p>

                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Issuing Body
                      </h4>
                      <p className="text-gray-300">{certData.issuing_body}</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Study Hours
                      </h4>
                      <p className="text-gray-300">{certData.study_hours}</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Cost Range
                      </h4>
                      <p className="text-gray-300">{certData.cost_range}</p>
                    </div>

                    {certData.prerequisites && certData.prerequisites.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-400 mb-1">
                          Prerequisites
                        </h4>
                        <ul className="list-disc list-inside text-gray-300 text-sm">
                          {certData.prerequisites.map((prereq, idx) => (
                            <li key={idx}>{prereq}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div>
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Exam Format
                      </h4>
                      <p className="text-gray-300">{certData.exam_format}</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-gray-400 mb-1">
                        Continuing Education
                      </h4>
                      <p className="text-gray-300">{certData.continuing_education}</p>
                    </div>

                    {certData.career_benefits && certData.career_benefits.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-400 mb-1">
                          Career Benefits
                        </h4>
                        <ul className="list-disc list-inside text-gray-300 text-sm">
                          {certData.career_benefits.map((benefit, idx) => (
                            <li key={idx}>{benefit}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  Select a certification to view details
                </div>
              )}
            </>
          )}

          {!selectedRole && !selectedCertification && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <span className="text-4xl mb-4">👆</span>
              <p className="text-gray-400">
                Select a {viewMode === 'roles' ? 'role' : 'certification'} to view details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfessionalRolesGuide;
