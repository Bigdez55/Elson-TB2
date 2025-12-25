import React from 'react';

interface CompanyDetails {
  name: string;
  symbol: string;
  description: string;
  ceo: string;
  founded: string;
  headquarters: string;
  employees: string;
  website?: string;
  industry?: string;
}

interface NewsItem {
  id: string;
  title: string;
  source: string;
  publishedAt: string;
  url?: string;
}

interface CompanyInfoProps {
  company: CompanyDetails;
  news: NewsItem[];
  className?: string;
}

export const CompanyInfo: React.FC<CompanyInfoProps> = ({
  company,
  news,
  className = '',
}) => {
  const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Less than 1 hour ago';
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  };

  return (
    <div className={`bg-gray-900 rounded-xl p-6 lg:col-span-2 ${className}`}>
      <h3 className="text-lg font-medium text-white mb-4">About {company.name}</h3>
      
      {/* Company Description */}
      <p className="text-gray-300 text-sm mb-4">
        {company.description}
      </p>
      
      {/* Company Details Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <h4 className="text-gray-400 text-sm">CEO</h4>
          <p className="text-white">{company.ceo}</p>
        </div>
        <div>
          <h4 className="text-gray-400 text-sm">Founded</h4>
          <p className="text-white">{company.founded}</p>
        </div>
        <div>
          <h4 className="text-gray-400 text-sm">Headquarters</h4>
          <p className="text-white">{company.headquarters}</p>
        </div>
        <div>
          <h4 className="text-gray-400 text-sm">Employees</h4>
          <p className="text-white">{company.employees}</p>
        </div>
        {company.industry && (
          <div>
            <h4 className="text-gray-400 text-sm">Industry</h4>
            <p className="text-white">{company.industry}</p>
          </div>
        )}
        {company.website && (
          <div>
            <h4 className="text-gray-400 text-sm">Website</h4>
            <a 
              href={company.website} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-purple-400 hover:text-purple-300 transition-colors"
            >
              {company.website.replace(/^https?:\/\//, '')}
            </a>
          </div>
        )}
      </div>
      
      {/* Recent News Section */}
      <div>
        <h3 className="text-lg font-medium text-white mb-4">Recent News</h3>
        <div className="space-y-3">
          {news.length > 0 ? (
            news.map((article) => (
              <div key={article.id} className="bg-gray-800 p-3 rounded-lg">
                <h4 className="text-white text-sm font-medium">{article.title}</h4>
                <div className="flex justify-between items-center mt-1">
                  <p className="text-gray-400 text-xs">
                    {article.source} • {formatTimeAgo(article.publishedAt)}
                  </p>
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300 text-xs transition-colors"
                    >
                      Read More
                    </a>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="bg-gray-800 p-3 rounded-lg">
              <p className="text-gray-400 text-sm">No recent news available for {company.symbol}</p>
            </div>
          )}
        </div>
        
        {/* View More News Button */}
        {news.length > 0 && (
          <div className="mt-4 text-center">
            <button className="text-purple-400 hover:text-purple-300 text-sm transition-colors">
              View More News
            </button>
          </div>
        )}
      </div>

      {/* Key Metrics Section */}
      <div className="mt-6 pt-6 border-t border-gray-800">
        <h3 className="text-lg font-medium text-white mb-4">Investment Highlights</h3>
        <div className="grid grid-cols-1 gap-3">
          <div className="bg-gray-800 p-3 rounded-lg">
            <div className="flex items-center">
              <svg className="h-4 w-4 text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-gray-300 text-sm">Market leader in electric vehicles</span>
            </div>
          </div>
          <div className="bg-gray-800 p-3 rounded-lg">
            <div className="flex items-center">
              <svg className="h-4 w-4 text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-gray-300 text-sm">Strong growth in energy storage</span>
            </div>
          </div>
          <div className="bg-gray-800 p-3 rounded-lg">
            <div className="flex items-center">
              <svg className="h-4 w-4 text-yellow-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-gray-300 text-sm">High volatility and regulatory risks</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};