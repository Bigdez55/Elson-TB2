import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAccessibility } from '../../hooks/useAccessibility';

/**
 * Mobile-optimized Learning component
 * Provides a touch-friendly learning experience for small screens
 */
const MobileLearning: React.FC = () => {
  const [activeModule, setActiveModule] = useState<string | null>(null);
  const [completedModules, setCompletedModules] = useState<string[]>([]);
  const [progress, setProgress] = useState<Record<string, number>>({});
  const { announce } = useAccessibility();
  const navigate = useNavigate();

  // Simulate fetching user's learning data
  useEffect(() => {
    // In a real app, this would be an API call
    setTimeout(() => {
      setCompletedModules(['stock-market-basics', 'types-of-investments']);
      setProgress({
        'trading-basics': 45,
        'technical-analysis': 10,
        'portfolio-diversification': 0,
        'risk-management': 0,
      });
    }, 500);
  }, []);

  // Handle module selection
  const handleModuleSelect = (moduleId: string) => {
    setActiveModule(moduleId);
    announce(`${moduleId.replace(/-/g, ' ')} module selected`, false);
    
    // In a real app, this would navigate to the module
    navigate(`/learning?module=${moduleId}`);
  };

  // Modules data for the learning path
  const learningModules = [
    {
      id: 'stock-market-basics',
      title: 'Stock Market Basics',
      description: 'Learn how stocks work and what the stock market is.',
      duration: '15 min',
      level: 'Beginner',
      image: '/assets/images/modules/stock-market.jpg',
    },
    {
      id: 'types-of-investments',
      title: 'Types of Investments',
      description: 'Explore different investment vehicles like stocks, bonds, ETFs, and more.',
      duration: '20 min',
      level: 'Beginner',
      image: '/assets/images/modules/investment-types.jpg',
    },
    {
      id: 'trading-basics',
      title: 'Trading Basics',
      description: 'Understand how to place trades and different order types.',
      duration: '25 min',
      level: 'Beginner',
      image: '/assets/images/modules/trading-basics.jpg',
    },
    {
      id: 'technical-analysis',
      title: 'Technical Analysis',
      description: 'Learn to read charts and identify trading patterns.',
      duration: '30 min',
      level: 'Intermediate',
      image: '/assets/images/modules/technical-analysis.jpg',
    },
    {
      id: 'portfolio-diversification',
      title: 'Portfolio Diversification',
      description: 'Understand why and how to diversify your investments.',
      duration: '20 min',
      level: 'Intermediate',
      image: '/assets/images/modules/diversification.jpg',
    },
    {
      id: 'risk-management',
      title: 'Risk Management',
      description: 'Learn strategies to protect your portfolio from market downturns.',
      duration: '25 min',
      level: 'Advanced',
      image: '/assets/images/modules/risk-management.jpg',
    }
  ];

  // Learning paths
  const learningPaths = [
    {
      id: 'beginner-path',
      title: 'Beginner Investor',
      description: 'Perfect for first-time investors',
      modules: ['stock-market-basics', 'types-of-investments', 'trading-basics'],
      progress: 68,
    },
    {
      id: 'intermediate-path',
      title: 'Intermediate Investor',
      description: 'For those with some experience',
      modules: ['technical-analysis', 'portfolio-diversification'],
      progress: 5,
    },
    {
      id: 'advanced-path',
      title: 'Advanced Strategies',
      description: 'Advanced trading techniques',
      modules: ['risk-management'],
      progress: 0,
    }
  ];

  // Calculate overall progress
  const overallProgress = Math.round(
    Object.values(progress).reduce((sum, value) => sum + value, 0) / 
    Object.keys(progress).length + 
    (completedModules.length / learningModules.length) * 100
  );

  return (
    <div className="mobile-learning pb-16">
      {/* Header with progress */}
      <div className="bg-gray-900 p-4 rounded-xl mb-4">
        <h1 className="text-xl font-bold text-white mb-2">Learning Center</h1>
        
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-white">Overall Progress</span>
            <span className="text-white">{Math.min(100, overallProgress)}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2.5">
            <div 
              className="bg-purple-600 h-2.5 rounded-full" 
              style={{ width: `${Math.min(100, overallProgress)}%` }}
            ></div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-800 p-3 rounded-lg text-center">
            <p className="text-xs text-gray-400">Completed</p>
            <p className="text-lg font-bold text-white">{completedModules.length}</p>
          </div>
          <div className="bg-gray-800 p-3 rounded-lg text-center">
            <p className="text-xs text-gray-400">In Progress</p>
            <p className="text-lg font-bold text-white">{Object.keys(progress).filter(m => progress[m] > 0).length}</p>
          </div>
        </div>
      </div>
      
      {/* Learning Paths */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white mb-3 px-1">Learning Paths</h2>
        <div className="flex overflow-x-auto gap-3 pb-3 -mx-4 px-4 hide-scrollbar">
          {learningPaths.map(path => (
            <div 
              key={path.id}
              className="bg-gray-900 p-4 rounded-xl shadow-md flex-shrink-0 w-72 touch-pan-x"
            >
              <h3 className="text-base font-medium text-white mb-1">{path.title}</h3>
              <p className="text-gray-400 text-xs mb-3">{path.description}</p>
              
              <div className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-white">{path.progress}%</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-1.5">
                  <div 
                    className="bg-purple-600 h-1.5 rounded-full" 
                    style={{ width: `${path.progress}%` }}
                  ></div>
                </div>
              </div>
              
              <button 
                className="w-full py-2 bg-purple-700 text-white rounded-lg text-sm active:bg-purple-800 transition-colors"
                onClick={() => navigate(`/learning?path=${path.id}`)}
              >
                Continue Path
              </button>
            </div>
          ))}
        </div>
      </div>
      
      {/* Module Cards */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3 px-1">Learning Modules</h2>
        <div className="space-y-3">
          {learningModules.map(module => {
            const isCompleted = completedModules.includes(module.id);
            const inProgress = progress[module.id] > 0;
            
            return (
              <div 
                key={module.id}
                className="bg-gray-900 rounded-xl overflow-hidden active:bg-gray-800 transition-colors"
                onClick={() => handleModuleSelect(module.id)}
              >
                <div className="relative h-32 bg-gray-800">
                  {/* Placeholder for module image */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg className="w-12 h-12 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                    </svg>
                  </div>
                  
                  {/* Module status indicator */}
                  {isCompleted && (
                    <div className="absolute top-2 right-2 bg-green-600 text-white text-xs font-medium px-2 py-1 rounded">
                      Completed
                    </div>
                  )}
                  
                  {inProgress && !isCompleted && (
                    <div className="absolute top-2 right-2 bg-yellow-600 text-white text-xs font-medium px-2 py-1 rounded">
                      In Progress
                    </div>
                  )}
                  
                  {/* Level indicator */}
                  <div className="absolute bottom-2 left-2 bg-gray-900 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                    {module.level}
                  </div>
                  
                  {/* Duration */}
                  <div className="absolute bottom-2 right-2 bg-gray-900 bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                    {module.duration}
                  </div>
                </div>
                
                <div className="p-4">
                  <h3 className="text-white font-medium mb-1">{module.title}</h3>
                  <p className="text-gray-400 text-xs mb-3">{module.description}</p>
                  
                  {/* Progress bar for in-progress modules */}
                  {inProgress && !isCompleted && (
                    <div className="w-full bg-gray-800 rounded-full h-1.5 mb-1">
                      <div 
                        className="bg-purple-600 h-1.5 rounded-full" 
                        style={{ width: `${progress[module.id]}%` }}
                      ></div>
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400">
                      {isCompleted ? 'Completed' : inProgress ? `${progress[module.id]}% complete` : 'Not started'}
                    </span>
                    <button className="text-purple-400 text-xs flex items-center">
                      {isCompleted ? 'Review' : inProgress ? 'Continue' : 'Start'} 
                      <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Quick Actions */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 px-4 py-3 z-10">
        <div className="flex justify-between">
          <button className="flex flex-col items-center justify-center text-xs text-purple-400 active:text-purple-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
            </svg>
            <span>Modules</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
            </svg>
            <span>Badges</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            <span>Notes</span>
          </button>
          <button className="flex flex-col items-center justify-center text-xs text-gray-400 active:text-gray-300 transition-colors w-1/4">
            <svg className="h-6 w-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            </svg>
            <span>Resources</span>
          </button>
        </div>
      </div>
      
      {/* Accessibility - Skip to content link */}
      <div className="sr-only">
        <a href="#main-content" className="skip-nav">Skip to main content</a>
      </div>
    </div>
  );
};

export default MobileLearning;