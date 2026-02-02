import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';

const Application: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const totalSteps = 3;

  const location = useLocation();
  const { user, refreshData } = useApp();
  const petId = location.state?.petId;

  // 检查用户是否已登录
  useEffect(() => {
    if (!user) {
      alert('请先登录后再提交领养申请');
      navigate('/login');
    }
  }, [user, navigate]);

  // Form State
  const [formData, setFormData] = useState({
    fullName: '',
    phone: '',
    occupation: '',
    housing: '',
    hasExperience: false,
    reason: ''
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { id, value } = e.target;
    setFormData(prev => ({ ...prev, [id]: value }));
  };

  const handleExperienceChange = (hasExp: boolean) => {
    setFormData(prev => ({ ...prev, hasExperience: hasExp }));
  };

  const handleNext = async () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      // Submit logic
      if (!user) {
        alert("请先登录后再提交领养申请");
        navigate('/login');
        return;
      }
      if (!petId) {
        alert("出错：无法获取宠物信息");
        return;
      }

      // Basic validation
      if (!formData.fullName || !formData.phone) {
        alert("请填写基本信息");
        setStep(1);
        return;
      }

      try {
        // 检查宠物是否已被领养
        const petResponse = await api.getPet(petId);
        if (petResponse.isAdopted) {
          alert("抱歉，该宠物已被领养，无法再提交申请。");
          navigate(`/details/${petId}`);
          return;
        }

        // 检查是否已经有对该宠物的申请
        const existingApplications = await api.getApplications(user.id);
        const existingAppForThisPet = existingApplications.find(
          app => app.pet_id === petId && app.status !== 'rejected'
        );
        if (existingAppForThisPet) {
          alert("您已经对此宠物提交过申请，无需重复提交。");
          navigate(`/details/${petId}`);
          return;
        }

        await api.submitApplication({
          pet_id: petId,
          user_id: user.id,
          full_name: formData.fullName,
          phone: formData.phone,
          occupation: formData.occupation,
          housing: formData.housing,
          has_experience: formData.hasExperience,
          reason: formData.reason
        });
        await refreshData();
        alert("申请已提交！我们会尽快联系您。");
        navigate('/');
      } catch (e: any) {
        console.error(e);
        alert("提交失败：" + e.message);
      }
    }
  };

  const renderStepContent = () => {
    switch (step) {
      case 1:
        return (
          <div className="flex flex-col gap-5 animate-in fade-in slide-in-from-right-2 duration-200">
            <div className="space-y-2">
              <label className="text-text-main dark:text-text-main-dark text-base font-medium leading-normal block" htmlFor="fullName">真实姓名</label>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-text-muted dark:text-text-muted group-focus-within:text-primary pointer-events-none">person</span>
                <input
                  className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl text-text-main dark:text-text-main-dark border border-gray-200 dark:border-gray-700 bg-card-light dark:bg-surface-dark focus:border-primary focus:ring-1 focus:ring-primary h-14 placeholder:text-text-muted/60 dark:placeholder:text-text-muted/60 pl-12 pr-4 text-base font-normal leading-normal transition-all shadow-sm focus:outline-none"
                  id="fullName"
                  placeholder="例如：张三"
                  type="text"
                  value={formData.fullName}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-text-main dark:text-text-main-dark text-base font-medium leading-normal block" htmlFor="phone">手机号码</label>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-text-muted dark:text-text-muted group-focus-within:text-primary pointer-events-none">call</span>
                <input
                  className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl text-text-main dark:text-text-main-dark border border-gray-200 dark:border-gray-700 bg-card-light dark:bg-surface-dark focus:border-primary focus:ring-1 focus:ring-primary h-14 placeholder:text-text-muted/60 dark:placeholder:text-text-muted/60 pl-12 pr-4 text-base font-normal leading-normal transition-all shadow-sm focus:outline-none"
                  id="phone"
                  placeholder="138 0000 0000"
                  type="tel"
                  value={formData.phone}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-text-main dark:text-text-main-dark text-base font-medium leading-normal block" htmlFor="occupation">职业</label>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-text-muted dark:text-text-muted group-focus-within:text-primary pointer-events-none">work</span>
                <input
                  className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl text-text-main dark:text-text-main-dark border border-gray-200 dark:border-gray-700 bg-card-light dark:bg-surface-dark focus:border-primary focus:ring-1 focus:ring-primary h-14 placeholder:text-text-muted/60 dark:placeholder:text-text-muted/60 pl-12 pr-4 text-base font-normal leading-normal transition-all shadow-sm focus:outline-none"
                  id="occupation"
                  placeholder="例如：设计师"
                  type="text"
                  value={formData.occupation}
                  onChange={handleInputChange}
                />
              </div>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="flex flex-col gap-5 animate-in fade-in slide-in-from-right-2 duration-200">
            <div className="space-y-2">
              <label className="text-text-main dark:text-text-main-dark text-base font-medium leading-normal block" htmlFor="housing">居住类型</label>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-text-muted dark:text-text-muted group-focus-within:text-primary pointer-events-none">home</span>
                <select
                  className="form-select flex w-full min-w-0 flex-1 overflow-hidden rounded-xl text-text-main dark:text-text-main-dark border border-gray-200 dark:border-gray-700 bg-card-light dark:bg-surface-dark focus:border-primary focus:ring-1 focus:ring-primary h-14 pl-12 pr-10 text-base font-normal leading-normal transition-all shadow-sm cursor-pointer appearance-none focus:outline-none"
                  id="housing"
                  value={formData.housing}
                  onChange={handleInputChange}
                >
                  <option disabled value="">请选择居住类型</option>
                  <option value="apartment">公寓</option>
                  <option value="house">独栋住宅</option>
                  <option value="villa">别墅</option>
                  <option value="condo">商品房</option>
                  <option value="other">其他</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-text-main dark:text-text-main-dark text-base font-medium leading-normal block">是否有养宠经验？</label>
              <div className="flex gap-4">
                <label className="flex-1 cursor-pointer">
                  <input
                    type="radio"
                    name="experience"
                    className="peer sr-only"
                    checked={formData.hasExperience}
                    onChange={() => handleExperienceChange(true)}
                  />
                  <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center peer-checked:border-primary peer-checked:bg-primary/10 transition-all hover:bg-gray-50 dark:hover:bg-white/5">
                    <span className="font-medium text-text-main dark:text-text-main-dark">有经验</span>
                  </div>
                </label>
                <label className="flex-1 cursor-pointer">
                  <input
                    type="radio"
                    name="experience"
                    className="peer sr-only"
                    checked={!formData.hasExperience}
                    onChange={() => handleExperienceChange(false)}
                  />
                  <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center peer-checked:border-primary peer-checked:bg-primary/10 transition-all hover:bg-gray-50 dark:hover:bg-white/5">
                    <span className="font-medium text-text-main dark:text-text-main-dark">我是新手</span>
                  </div>
                </label>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-text-main dark:text-text-main-dark text-base font-medium leading-normal block" htmlFor="reason">领养理由</label>
              <textarea
                className="w-full rounded-xl text-text-main dark:text-text-main-dark border border-gray-200 dark:border-gray-700 bg-card-light dark:bg-surface-dark focus:border-primary focus:ring-1 focus:ring-primary p-4 text-base font-normal leading-normal transition-all shadow-sm focus:outline-none resize-none"
                id="reason"
                rows={4}
                placeholder="请简述您为什么要领养这只宠物..."
                value={formData.reason}
                onChange={handleInputChange}
              />
            </div>
          </div>
        );
      case 3:
        const housingLabels: { [key: string]: string } = {
          apartment: '公寓',
          house: '独栋住宅',
          villa: '别墅',
          condo: '商品房',
          other: '其他'
        };
        return (
          <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-right-4 duration-300 items-center text-center py-4">
            <div className="w-24 h-24 rounded-full bg-secondary/10 flex items-center justify-center">
              <span className="material-symbols-outlined text-secondary text-5xl">check_circle</span>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-text-main dark:text-text-main-dark mb-2">确认提交申请？</h3>
              <p className="text-text-muted dark:text-text-muted">请确认您填写的信息真实有效。提交后，我们的协调员将在24小时内与您联系。</p>
            </div>
            <div className="w-full bg-card-light dark:bg-card-dark p-4 rounded-xl text-left border border-gray-100 dark:border-gray-800">
              <div className="flex justify-between mb-2">
                <span className="text-gray-500 text-sm">申请人</span>
                <span className="font-medium">{formData.fullName || '未填写'}</span>
              </div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-500 text-sm">联系方式</span>
                <span className="font-medium">{formData.phone || '未填写'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 text-sm">居住类型</span>
                <span className="font-medium">{housingLabels[formData.housing] || '未选择'}</span>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  const getStepTitle = () => {
    switch (step) {
      case 1: return "基本信息";
      case 2: return "家庭环境";
      case 3: return "确认提交";
      default: return "";
    }
  };

  const progressPercentage = (step / totalSteps) * 100;

  return (
    <div className="relative flex h-full min-h-screen w-full flex-col overflow-x-hidden max-w-md mx-auto shadow-xl bg-background-light dark:bg-background-dark">
      {/* Header */}
      <header className="sticky top-0 z-50 flex items-center bg-background-light dark:bg-background-dark p-4 pb-2 justify-between backdrop-blur-md bg-opacity-90 dark:bg-opacity-90">
        <button
          onClick={() => {
            if (step > 1) setStep(step - 1);
            else navigate(-1);
          }}
          aria-label="Go back"
          className="text-text-main dark:text-text-main-dark flex size-12 shrink-0 items-center justify-center rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
        >
          <span className="material-symbols-outlined text-[24px]">arrow_back</span>
        </button>
        <h2 className="text-text-main dark:text-text-main-dark text-lg font-bold leading-tight tracking-[-0.015em] flex-1 text-center pr-12">领养申请</h2>
      </header>

      {/* Main Form */}
      <main className="flex-1 flex flex-col px-4 pb-24">
        {/* Progress */}
        <div className="flex flex-col gap-3 py-4">
          <div className="flex gap-6 justify-between items-end">
            <p className="text-text-main dark:text-text-main-dark text-base font-medium leading-normal">步骤 {step} / {totalSteps}</p>
            <span className="text-xs font-semibold text-text-muted dark:text-text-muted bg-primary/10 px-2 py-1 rounded-full">已完成 {Math.round(progressPercentage)}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
          <p className="text-text-muted dark:text-text-muted text-sm font-medium leading-normal">{getStepTitle()}</p>
        </div>

        {/* Title */}
        {step < 3 && (
          <div className="pt-2 pb-6">
            <h1 className="text-text-main dark:text-text-main-dark tracking-tight text-[28px] font-bold leading-tight pb-2">
              {step === 1 ? '让我们了解一下你！' : '关于您的家庭环境'}
            </h1>
            <p className="text-text-main/70 dark:text-text-main-dark/70 text-base font-normal leading-relaxed">
              {step === 1 ? '请提供一些基本信息，以便我们为您匹配最适合的毛孩子。' : '我们需要确认您的居住环境适合养宠。'}
            </p>
          </div>
        )}

        {/* Render Form Steps */}
        <form className="flex flex-col gap-5">
          {renderStepContent()}
        </form>

        <div className="h-8"></div>
      </main>

      {/* Floating Action Button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-lg border-t border-gray-200 dark:border-gray-700 z-40 max-w-md mx-auto">
        <button
          onClick={handleNext}
          className="w-full h-14 bg-primary hover:bg-opacity-90 active:scale-[0.98] transition-all rounded-xl flex items-center justify-center gap-2 group shadow-lg shadow-primary/20"
        >
          <span className="text-[#0f2906] text-lg font-bold">{step === totalSteps ? '提交申请' : '下一步'}</span>
          <span className="material-symbols-outlined text-[#0f2906] transition-transform group-hover:translate-x-1">{step === totalSteps ? 'send' : 'arrow_forward'}</span>
        </button>
      </div>

      {/* Background Decor */}
      <div aria-hidden="true" className="fixed inset-0 -z-10 overflow-hidden bg-neutral-100 dark:bg-neutral-900 pointer-events-none hidden md:block">
        <div className="absolute -top-[30%] -right-[10%] w-[70%] h-[70%] rounded-full bg-primary/20 blur-[120px]"></div>
        <div className="absolute top-[60%] -left-[10%] w-[50%] h-[50%] rounded-full bg-blue-400/10 blur-[100px]"></div>
      </div>
    </div>
  );
};

export default Application;