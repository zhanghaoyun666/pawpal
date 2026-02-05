import React, { useState, useEffect } from 'react';
import { aiApi, PreCheckResult, UserProfile } from '../services/aiApi';

interface AIPrecheckProps {
  applicationId: string;
  applicationData: Record<string, any>;
  userProfile: UserProfile;
  petId: string;
  onResult?: (result: PreCheckResult) => void;
}

const AIPrecheck: React.FC<AIPrecheckProps> = ({
  applicationId,
  applicationData,
  userProfile,
  petId,
  onResult
}) => {
  const [result, setResult] = useState<PreCheckResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showDetails, setShowDetails] = useState(false);

  const runPrecheck = async () => {
    setIsLoading(true);
    setError('');

    try {
      const precheckResult = await aiApi.precheckApplication(
        applicationId,
        applicationData,
        userProfile,
        petId
      );
      setResult(precheckResult);
      onResult?.(precheckResult);
    } catch (err: any) {
      setError(err.message || '预审失败');
    } finally {
      setIsLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-500 bg-green-50 dark:bg-green-900/20';
      case 'medium': return 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      case 'high': return 'text-red-500 bg-red-50 dark:bg-red-900/20';
      default: return 'text-gray-500 bg-gray-50';
    }
  };

  const getRiskText = (level: string) => {
    switch (level) {
      case 'low': return '低风险';
      case 'medium': return '中风险';
      case 'high': return '高风险';
      default: return '未知';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin" />
          <div>
            <p className="font-bold">AI 正在审核...</p>
            <p className="text-sm text-gray-500">分析申请信息、用户画像和宠物需求</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-2xl p-6">
        <div className="flex items-center gap-2 text-red-500 mb-2">
          <span className="material-symbols-outlined">error</span>
          <span className="font-bold">AI 审核失败</span>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{error}</p>
        <button
          onClick={runPrecheck}
          className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-bold"
        >
          重试
        </button>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-gradient-to-r from-primary/10 to-secondary/10 rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-[#0f2906] text-2xl">smart_toy</span>
          </div>
          <div className="flex-1">
            <h3 className="font-bold mb-1">AI 预审助手</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              让 AI 自动分析申请资质，识别潜在风险，生成审核建议。人工只需复核即可。
            </p>
            <button
              onClick={runPrecheck}
              className="px-4 py-2 bg-primary text-[#0f2906] rounded-xl font-bold text-sm"
            >
              开始 AI 预审
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-2xl p-6 ${
      result.auto_approved 
        ? 'bg-green-50 dark:bg-green-900/20 border-2 border-green-200' 
        : 'bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-200'
    }`}>
      {/* Header */}
      <div className="flex items-start gap-4 mb-4">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
          result.auto_approved ? 'bg-green-500' : 'bg-yellow-500'
        }`}>
          <span className="material-symbols-outlined text-white text-2xl">
            {result.auto_approved ? 'check_circle' : 'person_search'}
          </span>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-bold">AI 预审结果</h3>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${getRiskColor(result.risk_level)}`}>
              {getRiskText(result.risk_level)}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            综合评分: <span className="font-bold text-lg">{result.score}</span>/100
            {result.auto_approved && ' · 建议自动通过'}
          </p>
        </div>
      </div>

      {/* Quick Summary */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 mb-4">
        <p className="text-sm">{result.review_report}</p>
      </div>

      {/* Risk Points */}
      {result.risk_points.length > 0 && (
        <div className="mb-4">
          <h4 className="font-bold text-sm mb-2 flex items-center gap-1">
            <span className="material-symbols-outlined text-red-500 text-base">warning</span>
            风险点 ({result.risk_points.length})
          </h4>
          <div className="space-y-2">
            {result.risk_points.map((point, idx) => (
              <div key={idx} className="bg-white dark:bg-gray-800 rounded-lg p-3 text-sm">
                <span className="font-medium text-red-500">{point.field}:</span>{' '}
                <span className="text-gray-600 dark:text-gray-400">{point.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <div className="mb-4">
          <h4 className="font-bold text-sm mb-2 flex items-center gap-1">
            <span className="material-symbols-outlined text-blue-500 text-base">lightbulb</span>
            建议
          </h4>
          <ul className="space-y-1">
            {result.suggestions.map((suggestion, idx) => (
              <li key={idx} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                <span className="text-primary">•</span>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="flex-1 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-bold"
        >
          {showDetails ? '收起详情' : '查看详情'}
        </button>
        <button
          onClick={runPrecheck}
          className="flex-1 py-2 bg-primary text-[#0f2906] rounded-xl text-sm font-bold"
        >
          重新审核
        </button>
      </div>

      {/* Details */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="font-bold text-sm mb-2">审核维度</h4>
          <div className="space-y-2">
            {[
              { key: 'living', label: '居住条件', score: 85 },
              { key: 'experience', label: '经验匹配', score: result.user_profile?.experience_level === 'experienced' ? 90 : 60 },
              { key: 'time', label: '时间投入', score: (result.user_profile?.daily_time_available || 0) > 2 ? 80 : 50 },
              { key: 'motivation', label: '领养动机', score: 75 },
            ].map(item => (
              <div key={item.key} className="flex items-center gap-2">
                <span className="text-xs text-gray-500 w-20">{item.label}</span>
                <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${item.score}%` }}
                  />
                </div>
                <span className="text-xs text-gray-400 w-8 text-right">{item.score}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIPrecheck;
