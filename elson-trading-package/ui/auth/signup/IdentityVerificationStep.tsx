import React from 'react';
import Input from '../../common/Input';
import Select from '../../common/Select';
import Button from '../../common/Button';
import { FiInfo, FiUpload } from 'react-icons/fi';

interface IdentityVerificationStepProps {
  ssn: string;
  dob: string;
  streetAddress: string;
  aptSuite: string;
  city: string;
  state: string;
  zipCode: string;
  idType: string;
  certifyInfo: boolean;
  setSsn: (value: string) => void;
  setDob: (value: string) => void;
  setStreetAddress: (value: string) => void;
  setAptSuite: (value: string) => void;
  setCity: (value: string) => void;
  setState: (value: string) => void;
  setZipCode: (value: string) => void;
  setIdType: (value: string) => void;
  setCertifyInfo: (value: boolean) => void;
  validationError: string | null;
  validateStep: () => boolean;
}

const IdentityVerificationStep: React.FC<IdentityVerificationStepProps> = ({
  ssn,
  dob,
  streetAddress,
  aptSuite,
  city,
  state,
  zipCode,
  idType,
  certifyInfo,
  setSsn,
  setDob,
  setStreetAddress,
  setAptSuite,
  setCity,
  setState,
  setZipCode,
  setIdType,
  setCertifyInfo,
  validationError,
}) => {
  // Format SSN as user types
  const handleSsnChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '');
    let formattedValue = '';
    
    if (value.length > 0) {
      formattedValue = value.substring(0, 3);
      if (value.length > 3) {
        formattedValue += '-' + value.substring(3, 5);
      }
      if (value.length > 5) {
        formattedValue += '-' + value.substring(5, 9);
      }
    }
    
    setSsn(formattedValue);
  };
  
  // Format Date of Birth as user types
  const handleDobChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '');
    let formattedValue = '';
    
    if (value.length > 0) {
      formattedValue = value.substring(0, 2);
      if (value.length > 2) {
        formattedValue += '/' + value.substring(2, 4);
      }
      if (value.length > 4) {
        formattedValue += '/' + value.substring(4, 8);
      }
    }
    
    setDob(formattedValue);
  };

  // ID type options for the dropdown
  const idTypeOptions = [
    { value: 'drivers-license', label: 'Driver\'s License' },
    { value: 'passport', label: 'Passport' },
    { value: 'state-id', label: 'State ID' }
  ];

  // State options for dropdown
  const stateOptions = [
    { value: 'AL', label: 'Alabama' },
    { value: 'AK', label: 'Alaska' },
    { value: 'AZ', label: 'Arizona' },
    { value: 'AR', label: 'Arkansas' },
    { value: 'CA', label: 'California' },
    { value: 'CO', label: 'Colorado' },
    { value: 'CT', label: 'Connecticut' },
    { value: 'DE', label: 'Delaware' },
    { value: 'DC', label: 'District Of Columbia' },
    { value: 'FL', label: 'Florida' },
    { value: 'GA', label: 'Georgia' },
    { value: 'HI', label: 'Hawaii' },
    { value: 'ID', label: 'Idaho' },
    { value: 'IL', label: 'Illinois' },
    { value: 'IN', label: 'Indiana' },
    { value: 'IA', label: 'Iowa' },
    { value: 'KS', label: 'Kansas' },
    { value: 'KY', label: 'Kentucky' },
    { value: 'LA', label: 'Louisiana' },
    { value: 'ME', label: 'Maine' },
    { value: 'MD', label: 'Maryland' },
    { value: 'MA', label: 'Massachusetts' },
    { value: 'MI', label: 'Michigan' },
    { value: 'MN', label: 'Minnesota' },
    { value: 'MS', label: 'Mississippi' },
    { value: 'MO', label: 'Missouri' },
    { value: 'MT', label: 'Montana' },
    { value: 'NE', label: 'Nebraska' },
    { value: 'NV', label: 'Nevada' },
    { value: 'NH', label: 'New Hampshire' },
    { value: 'NJ', label: 'New Jersey' },
    { value: 'NM', label: 'New Mexico' },
    { value: 'NY', label: 'New York' },
    { value: 'NC', label: 'North Carolina' },
    { value: 'ND', label: 'North Dakota' },
    { value: 'OH', label: 'Ohio' },
    { value: 'OK', label: 'Oklahoma' },
    { value: 'OR', label: 'Oregon' },
    { value: 'PA', label: 'Pennsylvania' },
    { value: 'RI', label: 'Rhode Island' },
    { value: 'SC', label: 'South Carolina' },
    { value: 'SD', label: 'South Dakota' },
    { value: 'TN', label: 'Tennessee' },
    { value: 'TX', label: 'Texas' },
    { value: 'UT', label: 'Utah' },
    { value: 'VT', label: 'Vermont' },
    { value: 'VA', label: 'Virginia' },
    { value: 'WA', label: 'Washington' },
    { value: 'WV', label: 'West Virginia' },
    { value: 'WI', label: 'Wisconsin' },
    { value: 'WY', label: 'Wyoming' }
  ];

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">Verify your identity</h2>
        <p className="text-gray-400">As required by regulations, we need to verify your identity</p>
      </div>

      <div className="bg-gray-800 rounded-xl p-6 mb-8">
        <div className="flex items-start">
          <div className="h-10 w-10 bg-purple-900 rounded-full flex items-center justify-center flex-shrink-0">
            <FiInfo className="h-5 w-5 text-purple-300" />
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
        onChange={handleSsnChange}
        placeholder="XXX-XX-XXXX"
        maxLength={11}
        required
      />

      <Input
        label="Date of Birth"
        type="text"
        value={dob}
        onChange={handleDobChange}
        placeholder="MM/DD/YYYY"
        maxLength={10}
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
          <Select
            value={state}
            onChange={(value) => setState(value)}
            options={stateOptions}
            placeholder="State"
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
          <FiUpload className="h-10 w-10 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-400 text-sm mb-2">Drag and drop your file here, or click to browse</p>
          <Button variant="secondary" size="sm">Browse Files</Button>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Upload ID Document (Back)</label>
        <div className="border-2 border-dashed border-gray-700 rounded-lg p-6 text-center">
          <FiUpload className="h-10 w-10 text-gray-500 mx-auto mb-3" />
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

      {validationError && (
        <div className="text-red-500 text-sm">
          {validationError}
        </div>
      )}
    </div>
  );
};

export default IdentityVerificationStep;