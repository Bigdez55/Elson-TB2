import React, { useState } from 'react';
import {
  useListContentQuery,
  useListLearningPathsQuery,
  useGetMyProgressQuery,
  useGetMyPermissionsQuery,
} from '../services/educationApi';
import { Skeleton } from '../components/common/Skeleton';
import { Card, CardHeader, TabGroup } from '../components/elson';
import { TargetIcon, CashIcon, TrendingIcon, DocumentIcon } from '../components/icons/ElsonIcons';
import { LEVEL_STYLES } from '../types/elson';

const LearnPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Courses');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');

  const tabs = ['Courses', 'Tools', 'Progress'];

  // Fetch data from API
  const { data: content = [], isLoading: contentLoading } = useListContentQuery({});
  const { data: learningPaths = [], isLoading: pathsLoading } = useListLearningPathsQuery({});
  const { data: progress = [], isLoading: progressLoading } = useGetMyProgressQuery();
  const { data: permissions = [], isLoading: permissionsLoading } = useGetMyPermissionsQuery();

  const isLoading = contentLoading || pathsLoading || progressLoading || permissionsLoading;

  // Filter content
  const filteredContent = content.filter((item) => {
    if (selectedLevel !== 'all' && item.level !== selectedLevel.toUpperCase()) return false;
    return true;
  });

  // Calculate statistics
  const totalContent = content.length;
  const completedContent = progress.filter(p => p.is_completed).length;
  const overallProgress = totalContent > 0 ? Math.round((completedContent / totalContent) * 100) : 0;

  const getLevelStyle = (level: string) => {
    const levelKey = level.charAt(0) + level.slice(1).toLowerCase() as keyof typeof LEVEL_STYLES;
    return LEVEL_STYLES[levelKey] || LEVEL_STYLES.Beginner;
  };

  const getContentProgress = (contentId: number) => {
    const contentProgress = progress.find(p => p.content_id === contentId);
    return contentProgress ? contentProgress.progress_percent : 0;
  };

  const isContentCompleted = (contentId: number) => {
    const contentProgress = progress.find(p => p.content_id === contentId);
    return contentProgress?.is_completed || false;
  };

  // Financial tools
  const tools = [
    { icon: TargetIcon, title: 'Retirement Calculator', desc: 'Plan your retirement savings' },
    { icon: CashIcon, title: 'Loan Calculator', desc: 'Calculate loan payments' },
    { icon: TrendingIcon, title: 'Investment Growth', desc: 'Project your investment growth' },
    { icon: DocumentIcon, title: 'Tax Estimator', desc: 'Estimate your tax burden' },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen p-4 md:p-6" style={{ backgroundColor: '#0D1B2A' }}>
        <div className="space-y-4">
          <Skeleton variant="text" width={200} height={28} />
          <Skeleton variant="rectangular" width="100%" height={400} className="rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-6 space-y-4 md:space-y-6" style={{ backgroundColor: '#0D1B2A' }}>
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Learn</h1>
        <p className="text-gray-400 text-sm">Build your financial knowledge</p>
      </div>

      <TabGroup tabs={tabs} value={activeTab} onChange={setActiveTab} />

      {activeTab === 'Courses' && (
        <>
          {/* Level Filter */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {['all', 'beginner', 'intermediate', 'advanced'].map((level) => (
              <button
                key={level}
                onClick={() => setSelectedLevel(level)}
                className={`px-4 py-2 rounded-lg text-sm font-medium min-h-[40px] whitespace-nowrap transition-all ${
                  selectedLevel === level
                    ? 'text-[#C9A227]'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
                style={selectedLevel === level ? { backgroundColor: 'rgba(201, 162, 39, 0.2)', border: '1px solid rgba(201, 162, 39, 0.3)' } : {}}
              >
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </button>
            ))}
          </div>

          {/* Courses Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredContent.length === 0 ? (
              <Card className="col-span-full p-8 text-center">
                <p className="text-gray-400 mb-4">No courses available yet.</p>
                <p className="text-sm text-gray-500">Check back soon for new learning materials!</p>
              </Card>
            ) : (
              filteredContent.map((item) => {
                const itemProgress = getContentProgress(item.id);
                const completed = isContentCompleted(item.id);
                const levelStyle = getLevelStyle(item.level);

                return (
                  <Card key={item.id} className="p-4 cursor-pointer">
                    <span
                      className="px-2 py-1 rounded text-xs font-medium"
                      style={levelStyle}
                    >
                      {item.level.charAt(0) + item.level.slice(1).toLowerCase()}
                    </span>
                    <h3 className="text-lg font-semibold text-white mt-3 mb-2">{item.title}</h3>
                    {item.description && (
                      <p className="text-sm text-gray-400 mb-4 line-clamp-2">{item.description}</p>
                    )}
                    <p className="text-sm text-gray-500 mb-4">
                      {item.estimated_minutes ? `${item.estimated_minutes} min` : 'Self-paced'}
                      {completed && <span className="text-green-400 ml-2">✓ Completed</span>}
                    </p>

                    {/* Progress Bar */}
                    {itemProgress > 0 && (
                      <div className="w-full rounded-full h-2 mb-4" style={{ backgroundColor: '#374151' }}>
                        <div
                          className="h-2 rounded-full transition-all"
                          style={{ width: `${itemProgress}%`, background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
                        />
                      </div>
                    )}

                    <button
                      className="w-full py-2 rounded-lg font-semibold text-[#0D1B2A] transition-all"
                      style={{ background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
                    >
                      {itemProgress === 0 ? 'Start Learning' : completed ? 'Review' : 'Continue'}
                    </button>
                  </Card>
                );
              })
            )}
          </div>
        </>
      )}

      {activeTab === 'Tools' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tools.map((tool, i) => (
            <Card key={i} className="p-6 cursor-pointer hover:border-[#C9A227]/40">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
              >
                <tool.icon className="w-6 h-6 text-[#C9A227]" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">{tool.title}</h3>
              <p className="text-sm text-gray-400">{tool.desc}</p>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'Progress' && (
        <Card className="p-6">
          <div className="text-center py-8">
            <div
              className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4"
              style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
            >
              <span className="text-2xl font-bold text-[#C9A227]">{completedContent}</span>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              {completedContent === 0 ? 'Get Started' : `Level ${Math.floor(completedContent / 3) + 1} Investor`}
            </h3>
            <p className="text-gray-400 mb-6">
              {completedContent === 0
                ? 'Start learning to track your progress'
                : `You've completed ${completedContent} courses and earned ${completedContent * 50} XP`
              }
            </p>
            <div className="w-full max-w-md mx-auto rounded-full h-3" style={{ backgroundColor: '#374151' }}>
              <div
                className="h-3 rounded-full transition-all"
                style={{ width: `${overallProgress}%`, background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">{overallProgress}% complete</p>

            {/* Learning Paths */}
            {learningPaths.length > 0 && (
              <div className="mt-8 text-left">
                <h4 className="text-lg font-semibold text-white mb-4">Learning Paths</h4>
                <div className="space-y-3">
                  {learningPaths.map((path) => (
                    <div
                      key={path.id}
                      className="p-4 rounded-xl cursor-pointer transition-all hover:border-[#C9A227]/40"
                      style={{ backgroundColor: '#1a2535', border: '1px solid rgba(201, 162, 39, 0.1)' }}
                    >
                      <h5 className="font-medium text-white mb-1">{path.title}</h5>
                      {path.description && (
                        <p className="text-sm text-gray-400">{path.description}</p>
                      )}
                      <p className="text-xs text-[#C9A227] mt-2">{path.items.length} items in path</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default LearnPage;
