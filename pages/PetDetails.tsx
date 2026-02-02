import React from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useApp } from '../context/AppContext';

const PetDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { pets, toggleFavorite, isFavorite, user } = useApp();

  const pet = pets.find(p => p.id === id);

  if (!pet) {
    return <div className="p-10 text-center">Pet not found</div>;
  }

  const isFav = isFavorite(pet.id);

  const handleBack = () => {
    // Rely on state passed from previous pages (Home, Favorites, Chat)
    // If we have state.from, we know there is a history entry to go back to.
    // This is more reliable than history.length for the "Apply -> Back -> Back" scenario.
    if (location.state?.from) {
      navigate(-1);
    } else {
      navigate('/', { replace: true });
    }
  };

  return (
    <div className="relative flex h-full min-h-screen w-full flex-col overflow-x-hidden pb-24 bg-background-light dark:bg-background-dark max-w-md mx-auto">
      {/* Header */}
      <div className="sticky top-0 z-50 flex items-center bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-sm p-4 pb-2 justify-between">
        <button
          onClick={handleBack}
          type="button"
          className="text-[#111b0d] dark:text-white flex size-12 shrink-0 items-center justify-center rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
        >
          <span className="material-symbols-outlined text-2xl">arrow_back</span>
        </button>
        <h2 className="text-[#111b0d] dark:text-white text-lg font-bold leading-tight tracking-[-0.015em] flex-1 text-center">宠物详情</h2>
        <div className="flex w-12 items-center justify-end">
          <button
            onClick={() => toggleFavorite(pet.id)}
            className={`flex size-12 items-center justify-center overflow-hidden rounded-full bg-transparent text-[#111b0d] dark:text-white transition-colors ${!user ? 'cursor-not-allowed opacity-50' : 'cursor-pointer hover:bg-black/5 dark:hover:bg-white/10'}`}
            disabled={!user}
            title={!user ? '请先登录' : ''}
          >
            <span className={`material-symbols-outlined text-2xl ${isFav ? 'text-red-500 filled' : ''}`}>favorite</span>
          </button>
        </div>
      </div>

      {/* Hero Image */}
      <div className="@container">
        <div className="@[480px]:px-4 @[480px]:py-3">
          <div
            className={`w-full bg-center bg-no-repeat bg-cover flex flex-col justify-end overflow-hidden bg-gray-200 dark:bg-gray-800 @[480px]:rounded-xl min-h-80 shadow-sm ${pet.isAdopted ? 'grayscale opacity-70' : ''}`}
            style={{ backgroundImage: `url("${pet.image}")` }}
          >
            {/* 已领养标签 */}
            {pet.isAdopted && (
              <div className="m-4 bg-red-500 text-white text-sm font-bold px-4 py-2 rounded-full inline-block">
                已领养
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Title & Price */}
      <div className="px-4 pt-6 pb-2 flex justify-between items-end">
        <div>
          <h1 className="text-[#111b0d] dark:text-white tracking-light text-[32px] font-bold leading-tight">{pet.name}</h1>
          <div className="flex items-center gap-1 mt-1 text-[#5e9a4c] dark:text-[#7fd466]">
            <span className="material-symbols-outlined text-lg">location_on</span>
            <span className="text-sm font-medium">{pet.distance}</span>
          </div>
        </div>
        {pet.price && (
          <div className="bg-primary/20 dark:bg-primary/10 text-primary-dark dark:text-primary px-3 py-1.5 rounded-lg text-sm font-bold">
            {pet.price}
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="px-4 py-4">
        <div className="grid grid-cols-3 gap-3">
          <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white dark:bg-[#1a2e15] shadow-sm border border-[#eef6ec] dark:border-[#2a4522]">
            <span className="text-[#5e9a4c] dark:text-[#7fd466] text-sm font-medium mb-1">年龄</span>
            <span className="text-[#111b0d] dark:text-white font-bold text-lg">{pet.age}</span>
          </div>
          <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white dark:bg-[#1a2e15] shadow-sm border border-[#eef6ec] dark:border-[#2a4522]">
            <span className="text-[#5e9a4c] dark:text-[#7fd466] text-sm font-medium mb-1">性别</span>
            <span className="text-[#111b0d] dark:text-white font-bold text-lg">{pet.gender === 'Male' ? '公' : (pet.gender === 'Female' ? '母' : '公')}</span>
          </div>
          <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white dark:bg-[#1a2e15] shadow-sm border border-[#eef6ec] dark:border-[#2a4522]">
            <span className="text-[#5e9a4c] dark:text-[#7fd466] text-sm font-medium mb-1">体重</span>
            <span className="text-[#111b0d] dark:text-white font-bold text-lg">{pet.weight || '暂无'}</span>
          </div>
        </div>
      </div>

      {/* Owner Info */}
      {pet.owner && (
        <div className="px-4 py-2">
          <div className="flex items-center justify-between p-3 rounded-xl bg-white dark:bg-[#1a2e15] shadow-sm border border-[#eef6ec] dark:border-[#2a4522]">
            <div className="flex items-center gap-3">
              <div
                className="size-12 rounded-full bg-gray-300 overflow-hidden bg-cover bg-center"
                style={{ backgroundImage: `url("${pet.owner.image}")` }}
              >
              </div>
              <div>
                <p className="text-[#111b0d] dark:text-white text-sm font-bold">{pet.owner.name}</p>
                <p className="text-[#5e9a4c] dark:text-[#7fd466] text-xs">
                  {pet.owner.role === 'coordinator' ? '送养人' : '领养人'}
                </p>
              </div>
            </div>
            <button
              onClick={() => navigate(`/chat/new?pet=${pet.id}`)}
              className="size-10 flex items-center justify-center rounded-full bg-primary/20 hover:bg-primary/30 text-primary-dark dark:text-primary transition-colors"
            >
              <span className="material-symbols-outlined text-xl">chat_bubble</span>
            </button>
          </div>
        </div>
      )}

      {/* Health Info */}
      <div className="px-4 py-2">
        <h2 className="text-[#111b0d] dark:text-white text-lg font-bold leading-tight tracking-[-0.015em] text-left pb-3 pt-4">健康状况</h2>
        <div className="grid grid-cols-[40%_1fr] gap-x-4">
          <div className="col-span-2 grid grid-cols-subgrid border-t border-t-[#d5e7cf] dark:border-t-[#2a4522] py-4 items-center">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#5e9a4c] dark:text-[#7fd466] text-[20px]">vaccines</span>
              <p className="text-[#5e9a4c] dark:text-[#7fd466] text-sm font-medium leading-normal whitespace-nowrap">是否接种疫苗</p>
            </div>
            <p className="text-[#111b0d] dark:text-white text-sm font-normal leading-normal text-right">{pet.health?.vaccinated ? '是' : '否'}</p>
          </div>
          <div className="col-span-2 grid grid-cols-subgrid border-t border-t-[#d5e7cf] dark:border-t-[#2a4522] py-4 items-center">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#5e9a4c] dark:text-[#7fd466] text-[20px]">medical_services</span>
              <p className="text-[#5e9a4c] dark:text-[#7fd466] text-sm font-medium leading-normal whitespace-nowrap">是否绝育</p>
            </div>
            <p className="text-[#111b0d] dark:text-white text-sm font-normal leading-normal text-right">{pet.health?.neutered ? '是' : '否'}</p>
          </div>
          <div className="col-span-2 grid grid-cols-subgrid border-t border-t-[#d5e7cf] dark:border-t-[#2a4522] py-4 items-center">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#5e9a4c] dark:text-[#7fd466] text-[20px]">pets</span>
              <p className="text-[#5e9a4c] dark:text-[#7fd466] text-sm font-medium leading-normal whitespace-nowrap">是否植入芯片</p>
            </div>
            <p className="text-[#111b0d] dark:text-white text-sm font-normal leading-normal text-right">{pet.health?.microchipped ? '是' : '否'}</p>
          </div>
        </div>
      </div>

      {/* Description */}
      <div className="px-4 pb-6">
        <h2 className="text-[#111b0d] dark:text-white text-lg font-bold leading-tight tracking-[-0.015em] text-left pb-2 pt-2">关于 {pet.name}</h2>
        <p className="text-[#111b0d]/80 dark:text-white/80 text-base font-normal leading-relaxed">
          {pet.description || "暂无描述。"}
        </p>
      </div>

      {/* Bottom Sticky Footer */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-md border-t border-[#d5e7cf] dark:border-[#2a4522] z-40 max-w-md mx-auto">
        <div className="flex gap-4 w-full">
          <button className="flex items-center justify-center size-14 rounded-2xl border border-[#d5e7cf] dark:border-[#2a4522] bg-transparent text-[#111b0d] dark:text-white hover:bg-black/5 dark:hover:bg-white/10 transition-colors">
            <span className="material-symbols-outlined text-2xl">ios_share</span>
          </button>
          <button
            onClick={() => {
              if (!user) {
                alert('请先登录');
                navigate('/login');
                return;
              }
              if (user?.role === 'coordinator' || pet.isAdopted) return;
              navigate('/application', { state: { petId: pet.id } });
            }}
            disabled={!user || user?.role === 'coordinator' || pet.isAdopted}
            className={`flex-1 h-14 rounded-2xl font-bold text-lg flex items-center justify-center gap-2 shadow-lg transition-all active:scale-[0.98] ${!user || user?.role === 'coordinator' || pet.isAdopted
              ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed shadow-none'
              : 'bg-primary hover:bg-primary/90 text-[#111b0d] shadow-primary/20'
              }`}
          >
            <span>{!user ? '请先登录' : pet.isAdopted ? '已被领养' : user?.role === 'coordinator' ? '送养人不可申请' : '申请领养'}</span>
            <span className="material-symbols-outlined">pets</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default PetDetails;