import React, { useState } from 'react';
import {
  useListContentQuery,
  useListLearningPathsQuery,
  useGetMyProgressQuery,
  useGetMyPermissionsQuery,
} from '../services/educationApi';

const LearnPage: React.FC = () => {
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  // Fetch data from API
  const { data: content = [], isLoading: contentLoading } = useListContentQuery({});
  const { data: learningPaths = [], isLoading: pathsLoading } = useListLearningPathsQuery({});
  const { data: progress = [], isLoading: progressLoading } = useGetMyProgressQuery();
  const { data: permissions = [], isLoading: permissionsLoading } = useGetMyPermissionsQuery();

  // Filter content
  const filteredContent = content.filter((item) => {
    if (selectedLevel !== 'all' && item.level !== selectedLevel.toUpperCase()) return false;
    if (selectedType !== 'all' && item.content_type !== selectedType.toUpperCase()) return false;
    return true;
  });

  // Calculate statistics
  const totalContent = content.length;
  const completedContent = progress.filter(p => p.is_completed).length;
  const overallProgress = totalContent > 0 ? Math.round((completedContent / totalContent) * 100) : 0;
  const grantedPermissions = permissions.filter(p => p.is_granted).length;

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'BEGINNER': return 'text-green-400 bg-green-900/30';
      case 'INTERMEDIATE': return 'text-yellow-400 bg-yellow-900/30';
      case 'ADVANCED': return 'text-red-400 bg-red-900/30';
      default: return 'text-gray-400 bg-gray-900/30';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'MODULE': return '📚';
      case 'QUIZ': return '📝';
      case 'ARTICLE': return '📄';
      case 'INTERACTIVE': return '🎮';
      case 'VIDEO': return '🎥';
      default: return '📖';
    }
  };

  const getContentProgress = (contentId: number) => {
    const contentProgress = progress.find(p => p.content_id === contentId);
    return contentProgress ? contentProgress.progress_percent : 0;
  };

  const isContentCompleted = (contentId: number) => {
    const contentProgress = progress.find(p => p.content_id === contentId);
    return contentProgress?.is_completed || false;
  };

  if (contentLoading || pathsLoading || progressLoading || permissionsLoading) {
    return (
      <div className="bg-gray-800 min-h-screen p-6 flex items-center justify-center">
        <div className="text-white text-xl">Loading educational content...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 min-h-screen p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Learning Hub</h1>
        <p className="text-gray-400">
          Master trading concepts and unlock advanced features through education
        </p>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl p-4">
          <div className="text-purple-300 text-sm mb-1">Overall Progress</div>
          <div className="text-3xl font-bold text-white">{overallProgress}%</div>
          <div className="text-purple-200 text-xs mt-1">{totalContent} items available</div>
        </div>
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl p-4">
          <div className="text-blue-300 text-sm mb-1">Content Completed</div>
          <div className="text-3xl font-bold text-white">{completedContent}</div>
          <div className="text-blue-200 text-xs mt-1">of {totalContent} total</div>
        </div>
        <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-xl p-4">
          <div className="text-green-300 text-sm mb-1">Learning Paths</div>
          <div className="text-3xl font-bold text-white">{learningPaths.length}</div>
          <div className="text-green-200 text-xs mt-1">paths available</div>
        </div>
        <div className="bg-gradient-to-br from-yellow-900 to-yellow-800 rounded-xl p-4">
          <div className="text-yellow-300 text-sm mb-1">Permissions Earned</div>
          <div className="text-3xl font-bold text-white">{grantedPermissions}</div>
          <div className="text-yellow-200 text-xs mt-1">of {permissions.length} total</div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-4">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Filter by Level:</label>
          <div className="flex flex-wrap gap-2">
            {['all', 'beginner', 'intermediate', 'advanced'].map((level) => (
              <button
                key={level}
                onClick={() => setSelectedLevel(level)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  selectedLevel === level
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-900 text-gray-400 hover:bg-gray-800'
                }`}
              >
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm text-gray-400 mb-2 block">Filter by Type:</label>
          <div className="flex flex-wrap gap-2">
            {['all', 'module', 'quiz', 'article', 'interactive', 'video'].map((type) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  selectedType === type
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-900 text-gray-400 hover:bg-gray-800'
                }`}
              >
                {getTypeIcon(type.toUpperCase())} {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Content List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">📚 Educational Content</h2>
            <span className="text-sm text-gray-400">{filteredContent.length} items</span>
          </div>

          {filteredContent.length === 0 ? (
            <div className="bg-gray-900 rounded-xl p-8 text-center">
              <p className="text-gray-400 mb-4">No educational content available yet.</p>
              <p className="text-sm text-gray-500">Check back soon for new learning materials!</p>
            </div>
          ) : (
            filteredContent.map((item) => {
              const itemProgress = getContentProgress(item.id);
              const completed = isContentCompleted(item.id);

              return (
                <div
                  key={item.id}
                  className="bg-gray-900 rounded-xl p-6 hover:bg-gray-800 transition-colors cursor-pointer"
                >
                  <div className="flex items-start space-x-4">
                    <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-3xl">{getTypeIcon(item.content_type)}</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getLevelColor(item.level)}`}>
                          {item.level}
                        </span>
                      </div>
                      {item.description && (
                        <p className="text-sm text-gray-400 mb-3">{item.description}</p>
                      )}
                      <div className="flex items-center space-x-4 text-sm text-gray-500 mb-3">
                        <span>📝 {item.content_type}</span>
                        {item.estimated_minutes && (
                          <span>⏱️ {item.estimated_minutes} min</span>
                        )}
                        {completed && (
                          <span className="text-green-400">✓ Completed</span>
                        )}
                      </div>

                      {/* Progress Bar */}
                      {itemProgress > 0 && (
                        <div className="mt-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-400">Progress</span>
                            <span className="text-xs text-white font-medium">{Math.round(itemProgress)}%</span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-purple-500 to-blue-500 rounded-full h-2 transition-all duration-300"
                              style={{ width: `${itemProgress}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <div className="mt-4">
                        <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                          {itemProgress === 0 ? 'Start Learning' : completed ? 'Review' : 'Continue'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Learning Paths */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-4">🎯 Learning Paths</h3>
            {learningPaths.length === 0 ? (
              <p className="text-sm text-gray-400">No learning paths available yet.</p>
            ) : (
              <div className="space-y-3">
                {learningPaths.map((path) => (
                  <div
                    key={path.id}
                    className="p-3 rounded-lg bg-gradient-to-r from-purple-900/50 to-blue-900/50 border border-purple-600/30 cursor-pointer hover:border-purple-500/50 transition-colors"
                  >
                    <h4 className="font-medium text-white mb-1">{path.title}</h4>
                    {path.description && (
                      <p className="text-xs text-gray-400 mb-2">{path.description}</p>
                    )}
                    <div className="text-xs text-purple-300">
                      {path.items.length} items in path
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Trading Permissions */}
          <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">🔓 Trading Permissions</h3>
            <p className="text-sm text-gray-200 mb-4">
              Complete educational content to unlock trading permissions
            </p>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="flex items-center justify-between">
                <span className="text-white text-sm font-medium">Granted:</span>
                <span className="text-green-300 text-lg font-bold">{grantedPermissions}/{permissions.length}</span>
              </div>
            </div>
          </div>

          {/* Study Tips */}
          <div className="bg-gray-900 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">💡 Study Tips</h3>
            <div className="space-y-2 text-sm text-gray-300">
              <div className="flex items-start space-x-2">
                <span>📌</span>
                <p>Set aside time daily for learning</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>📌</span>
                <p>Practice with paper trading after lessons</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>📌</span>
                <p>Complete quizzes to test knowledge</p>
              </div>
              <div className="flex items-start space-x-2">
                <span>📌</span>
                <p>Track progress through learning paths</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearnPage;
