import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { aiApi, MatchResult, UserProfile } from '../services/aiApi';
import { useApp } from '../context/AppContext';

const AIRecommendations: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useApp();
  const [recommendations, setRecommendations] = useState<MatchResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [userProfile, setUserProfile] = useState<UserProfile>(location.state?.profile || {});

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    fetchRecommendations();
  }, [user]);

  const fetchRecommendations = async () => {
    setIsLoading(true);
    setError('');

    try {
      // 如果没有画像，先提取
      let profile = userProfile;
      if (Object.keys(profile).length === 0) {
        // 这里可以从用户历史对话中提取，简化处理直接跳转问卷
        navigate('/ai-questionnaire');
        return;
      }

      const results = await aiApi.getRecommendations(user!.id, profile, 3);
      setRecommendations(results);
    } catch (err: any) {
      setError(err.message || '获取推荐失败');
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-orange-500';
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-100 dark:bg-green-900/30';
    if (score >= 60) return 'bg-yellow-100 dark:bg-yellow-900/30';
    return 'bg-orange-100 dark:bg-orange-900/30';
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-background-light dark:bg-background-dark">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-gray-500">AI 正在为您分析最佳匹配...</p>
        <p className="text-xs text-gray-400 mt-2">综合考虑您的生活方式、居住环境和偏好</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-background-light dark:bg-background-dark p-4">
        <span className="material-symbols-outlined text-4xl text-red-400 mb-4">error</span>
        <p className="text-gray-500 mb-4">{error}</p>
        <button
          onClick={fetchRecommendations}
          className="px-6 py-2 bg-primary text-[#0f2906] rounded-xl font-bold"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="bg-background-light dark:bg-background-dark min-h-screen pb-24">
      {/* Header */}
      <header className="bg-background-light dark:bg-background-dark border-b border-gray-200 dark:border-gray-800 p-4 sticky top-0 z-10">
        <div className="flex items-center justify-between max-w-md mx-auto">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full">
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
          <div className="text-center">
            <h1 className="text-lg font-bold">为您推荐</h1>
            <p className="text-xs text-gray-500">基于您的画像智能匹配</p>
          </div>
          <button 
            onClick={() => navigate('/ai-questionnaire')}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
            title="重新问卷"
          >
            <span className="material-symbols-outlined">refresh</span>
          </button>
        </div>
      </header>

      {/* User Profile Summary */}
      <div className="bg-gradient-to-r from-primary/10 to-secondary/10 p-4">
        <div className="max-w-md mx-auto">
          <h2 className="text-sm font-bold mb-2 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">person</span>
            您的画像
          </h2>
          <div className="flex flex-wrap gap-2">
            {userProfile.living_space && (
              <span className="px-2 py-1 bg-white dark:bg-gray-800 rounded-full text-xs">
                {userProfile.living_space === 'apartment' ? '公寓' : 
                 userProfile.living_space === 'house_with_yard' ? '带院子的房子' : '住宅'}
              </span>
            )}
            {userProfile.experience_level && (
              <span className="px-2 py-1 bg-white dark:bg-gray-800 rounded-full text-xs">
                {userProfile.experience_level === 'none' ? '新手' : 
                 userProfile.experience_level === 'beginner' ? '有一些经验' : '经验丰富'}
              </span>
            )}
            {userProfile.daily_time_available ? (
              <span className="px-2 py-1 bg-white dark:bg-gray-800 rounded-full text-xs">
                每天{userProfile.daily_time_available}小时
              </span>
            ) : null}
            {userProfile.family_status && (
              <span className="px-2 py-1 bg-white dark:bg-gray-800 rounded-full text-xs">
                {userProfile.family_status === 'single' ? '单身' : 
                 userProfile.family_status === 'couple' ? '夫妻' : 
                 userProfile.family_status === 'with_kids' ? '有小孩' : '有老人'}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <main className="p-4 max-w-md mx-auto space-y-4">
        {recommendations.length === 0 ? (
          <div className="text-center py-10">
            <span className="material-symbols-outlined text-4xl text-gray-300 mb-2">pets</span>
            <p className="text-gray-500">暂无推荐，请完善您的画像</p>
          </div>
        ) : (
          <>
            <p className="text-sm text-gray-500 text-center mb-4">
              根据您的画像，我们从 {recommendations.length} 只宠物中精选出最匹配的
            </p>

            {recommendations.map((match, index) => (
              <div
                key={match.pet_id}
                onClick={() => navigate(`/details/${match.pet_id}`)}
                className="bg-white dark:bg-card-dark rounded-2xl shadow-sm overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
              >
                {/* Rank Badge */}
                <div className="relative">
                  <div className={`absolute top-3 left-3 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                    index === 0 ? 'bg-yellow-400 text-yellow-900' :
                    index === 1 ? 'bg-gray-300 text-gray-700' :
                    'bg-orange-300 text-orange-800'
                  }`}>
                    {index + 1}
                  </div>
                  
                  {/* Match Score */}
                  <div className={`absolute top-3 right-3 px-3 py-1 rounded-full ${getScoreBg(match.score)}`}>
                    <span className={`font-bold ${getScoreColor(match.score)}`}>
                      {Math.round(match.score)}% 匹配
                    </span>
                  </div>

                  <img
                    src={match.pet_image}
                    alt={match.pet_name}
                    className="w-full h-48 object-cover"
                  />
                </div>

                <div className="p-4">
                  <h3 className="font-bold text-lg mb-2">{match.pet_name}</h3>

                  {/* Match Reasons */}
                  <div className="mb-3">
                    <p className="text-xs text-gray-500 mb-1">匹配理由</p>
                    <div className="flex flex-wrap gap-1">
                      {match.reasons.slice(0, 3).map((reason, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 text-xs rounded-full">
                          ✓ {reason}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Concerns */}
                  {match.concerns.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1">需要考虑</p>
                      <div className="flex flex-wrap gap-1">
                        {match.concerns.slice(0, 2).map((concern, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 text-xs rounded-full">
                            ! {concern}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Compatibility Breakdown */}
                  {match.compatibility && Object.keys(match.compatibility).length > 0 && (
                    <div className="space-y-1">
                      {Object.entries(match.compatibility).map(([key, value]) => (
                        <div key={key} className="flex items-center gap-2">
                          <span className="text-xs text-gray-500 w-16">
                            {key === 'activity' ? '活动量' :
                             key === 'space' ? '空间' :
                             key === 'experience' ? '经验' :
                             key === 'time' ? '时间' :
                             key === 'family' ? '家庭' : key}
                          </span>
                          <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{ width: `${(value as number) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400 w-8 text-right">
                            {Math.round((value as number) * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  <button className="w-full mt-4 py-2 bg-primary text-[#0f2906] rounded-xl font-bold text-sm hover:opacity-90 transition-opacity">
                    查看详情
                  </button>
                </div>
              </div>
            ))}

            {/* Browse All Button */}
            <button
              onClick={() => navigate('/')}
              className="w-full py-3 border-2 border-primary text-primary rounded-xl font-bold text-sm hover:bg-primary/5 transition-colors"
            >
              浏览全部宠物
            </button>
          </>
        )}
      </main>
    </div>
  );
};

export default AIRecommendations;
