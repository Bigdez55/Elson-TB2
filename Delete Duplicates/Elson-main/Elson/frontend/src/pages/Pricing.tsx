import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../app/components/common/Button';
import { Layout } from '../app/components/layout/Layout';

const PricingPage: React.FC = () => {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annually'>('monthly');
  const navigate = useNavigate();
  
  const handleUpgrade = (plan: string) => {
    navigate(`/settings?upgrade=${plan}`);
  };
  
  // Calculate prices based on billing cycle
  const getPricingDetails = () => {
    if (billingCycle === 'annually') {
      return {
        premium: {
          price: '$7.99',
          period: 'month',
          billedAs: 'Billed as $95.88 annually',
          savings: '20%'
        },
        family: {
          price: '$15.99',
          period: 'month',
          billedAs: 'Billed as $191.88 annually',
          savings: '20%'
        }
      };
    } else {
      return {
        premium: {
          price: '$9.99',
          period: 'month',
          billedAs: 'Billed monthly',
          savings: null
        },
        family: {
          price: '$19.99',
          period: 'month',
          billedAs: 'Billed monthly',
          savings: null
        }
      };
    }
  };
  
  const pricing = getPricingDetails();
  
  return (
    <Layout>
      <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight">
            Plans for Every Investor
          </h1>
          <p className="mt-4 text-xl text-gray-500 max-w-3xl mx-auto">
            Choose the plan that fits your needs. Upgrade or downgrade anytime.
          </p>
        </div>
        
        {/* Billing toggle */}
        <div className="flex justify-center mb-12">
          <div className="relative bg-gray-100 p-1 rounded-lg inline-flex">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`${
                billingCycle === 'monthly' 
                  ? 'bg-white shadow-sm' 
                  : 'bg-transparent hover:bg-gray-200'
              } relative rounded-md py-2 px-4 text-sm font-medium whitespace-nowrap focus:outline-none transition-colors duration-200`}
            >
              Monthly billing
            </button>
            <button
              onClick={() => setBillingCycle('annually')}
              className={`${
                billingCycle === 'annually' 
                  ? 'bg-white shadow-sm' 
                  : 'bg-transparent hover:bg-gray-200'
              } relative rounded-md py-2 px-4 text-sm font-medium whitespace-nowrap focus:outline-none transition-colors duration-200`}
            >
              Annual billing <span className="text-indigo-600 font-semibold">Save 20%</span>
            </button>
          </div>
        </div>
        
        {/* Pricing cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {/* Free tier */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-6">
              <h2 className="text-xl font-medium text-gray-900">Free</h2>
              <p className="mt-1 text-gray-500">Basic investing features</p>
              <p className="mt-4">
                <span className="text-4xl font-extrabold text-gray-900">$0</span>
                <span className="text-gray-500 ml-1">/forever</span>
              </p>
              <Button
                onClick={() => navigate('/register')}
                className="mt-6 w-full justify-center bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
              >
                Get started for free
              </Button>
            </div>
            <div className="px-6 pt-6 pb-8">
              <h3 className="text-sm font-medium text-gray-900 tracking-wide uppercase">
                What's included
              </h3>
              <ul className="mt-4 space-y-3">
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Commission-free trading</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Basic market data</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Paper trading</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Basic educational content</span>
                </li>
              </ul>
            </div>
          </div>
          
          {/* Premium tier */}
          <div className="bg-white border-2 border-indigo-600 rounded-lg shadow-sm overflow-hidden relative">
            <div className="absolute top-0 inset-x-0">
              <div className="bg-indigo-600 text-white text-xs font-semibold py-1 text-center">
                MOST POPULAR
              </div>
            </div>
            <div className="p-6 pt-8">
              <h2 className="text-xl font-medium text-gray-900">Premium</h2>
              <p className="mt-1 text-gray-500">Advanced trading features</p>
              <p className="mt-4">
                <span className="text-4xl font-extrabold text-gray-900">{pricing.premium.price}</span>
                <span className="text-gray-500 ml-1">/{pricing.premium.period}</span>
              </p>
              <p className="mt-1 text-sm text-gray-500">{pricing.premium.billedAs}</p>
              {pricing.premium.savings && (
                <p className="mt-1 text-sm font-medium text-indigo-600">
                  Save {pricing.premium.savings} with annual billing
                </p>
              )}
              <Button
                onClick={() => handleUpgrade('premium')}
                className="mt-6 w-full justify-center bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Upgrade to Premium
              </Button>
            </div>
            <div className="px-6 pt-6 pb-8">
              <h3 className="text-sm font-medium text-gray-900 tracking-wide uppercase">
                What's included
              </h3>
              <ul className="mt-4 space-y-3">
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Everything in Free plan</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700"><span className="font-semibold">Unlimited</span> recurring investments</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Advanced market data</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">AI trading recommendations</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Tax-loss harvesting</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">High-yield savings (5.00% APY)</span>
                </li>
              </ul>
            </div>
          </div>
          
          {/* Family tier */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="p-6">
              <h2 className="text-xl font-medium text-gray-900">Family Premium</h2>
              <p className="mt-1 text-gray-500">For families investing together</p>
              <p className="mt-4">
                <span className="text-4xl font-extrabold text-gray-900">{pricing.family.price}</span>
                <span className="text-gray-500 ml-1">/{pricing.family.period}</span>
              </p>
              <p className="mt-1 text-sm text-gray-500">{pricing.family.billedAs}</p>
              {pricing.family.savings && (
                <p className="mt-1 text-sm font-medium text-indigo-600">
                  Save {pricing.family.savings} with annual billing
                </p>
              )}
              <Button
                onClick={() => handleUpgrade('family')}
                className="mt-6 w-full justify-center bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Upgrade to Family
              </Button>
            </div>
            <div className="px-6 pt-6 pb-8">
              <h3 className="text-sm font-medium text-gray-900 tracking-wide uppercase">
                What's included
              </h3>
              <ul className="mt-4 space-y-3">
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Everything in Premium plan</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700"><span className="font-semibold">Up to 5</span> custodial accounts</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Family investment challenges</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Age-appropriate educational content</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Guardian approval workflow</span>
                </li>
                <li className="flex">
                  <svg className="flex-shrink-0 h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="ml-2 text-gray-700">Multiple retirement accounts</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
        
        {/* FAQ section */}
        <div className="mt-20 max-w-3xl mx-auto">
          <h2 className="text-3xl font-extrabold text-gray-900 text-center mb-10">
            Frequently Asked Questions
          </h2>
          
          <dl className="space-y-8">
            <div>
              <dt className="text-lg font-semibold text-gray-900">
                Can I switch plans later?
              </dt>
              <dd className="mt-2 text-gray-500">
                Yes, you can upgrade, downgrade, or cancel your plan at any time. 
                If you downgrade, your Premium features will remain active until the end of your current billing period.
              </dd>
            </div>
            
            <div>
              <dt className="text-lg font-semibold text-gray-900">
                How do custodial accounts work?
              </dt>
              <dd className="mt-2 text-gray-500">
                Custodial accounts allow you to invest on behalf of minors. As the guardian, you maintain 
                control over the account until the minor reaches the age of majority in their state.
                With the Family plan, you can create up to 5 custodial accounts.
              </dd>
            </div>
            
            <div>
              <dt className="text-lg font-semibold text-gray-900">
                What's the high-yield savings account?
              </dt>
              <dd className="mt-2 text-gray-500">
                Our high-yield savings account offers a competitive 5.00% APY, significantly higher than traditional banks.
                Your money remains liquid and FDIC-insured up to $250,000. This feature is available to Premium and Family subscribers.
              </dd>
            </div>
            
            <div>
              <dt className="text-lg font-semibold text-gray-900">
                How is tax-loss harvesting handled?
              </dt>
              <dd className="mt-2 text-gray-500">
                Our automated tax-loss harvesting algorithm identifies opportunities to offset capital gains with losses,
                potentially reducing your tax liability. The system follows wash sale rules and rebalances your portfolio 
                to maintain your target asset allocation.
              </dd>
            </div>
            
            <div>
              <dt className="text-lg font-semibold text-gray-900">
                Do you offer a discount for educational institutions?
              </dt>
              <dd className="mt-2 text-gray-500">
                Yes! We offer special pricing for schools and educational institutions. 
                Contact our enterprise sales team at enterprise@elson.com for more information.
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </Layout>
  );
};

export default PricingPage;