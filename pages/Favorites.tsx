import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import BottomNav from '../components/BottomNav';

const Favorites: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { pets, favorites, toggleFavorite, user } = useApp();
  
  const favoritePets = pets.filter(pet => favorites.includes(pet.id));

  return (
    <div className="relative flex h-full min-h-screen w-full flex-col overflow-x-hidden bg-background-light dark:bg-background-dark max-w-md mx-auto pb-24">
      <header className="sticky top-0 z-10 flex items-center bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-sm p-4 border-b border-gray-100 dark:border-gray-800">
        <h2 className="text-text-main dark:text-white text-xl font-bold leading-tight tracking-[-0.015em] flex-1 text-center">我的收藏</h2>
      </header>

      <main className="p-4">
        {!user ? (
          <div className="flex flex-col items-center justify-center pt-20 text-gray-400 dark:text-gray-500">
            <div className="w-20 h-20 bg-gray-100 dark:bg-card-dark rounded-full flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-4xl">lock</span>
            </div>
            <p className="text-lg font-medium">请先登录</p>
            <p className="text-sm mt-2">登录后才能查看收藏的宠物</p>
            <button 
              onClick={() => navigate('/login')}
              className="mt-6 px-6 py-2 bg-primary text-text-main font-bold rounded-xl shadow-sm hover:opacity-90 transition-opacity"
            >
              去登录
            </button>
          </div>
        ) : favoritePets.length > 0 ? (
          <div className="grid grid-cols-2 gap-4">
            {favoritePets.map((pet) => (
              <div 
                key={pet.id} 
                onClick={() => navigate(`/details/${pet.id}`, { state: { from: location.pathname } })}
                className="bg-card-light dark:bg-card-dark p-3 rounded-2xl shadow-sm hover:shadow-md transition-shadow cursor-pointer group"
              >
                <div className="relative h-40 w-full rounded-xl overflow-hidden mb-3">
                  <img 
                    alt={pet.name} 
                    className={`w-full h-full object-cover transform transition-transform duration-500 ${pet.isAdopted ? 'grayscale opacity-70' : 'group-hover:scale-105'}`} 
                    src={pet.image}
                  />
                  
                  {/* 已领养标签 */}
                  {pet.isAdopted && (
                    <div className="absolute left-2 bottom-2 bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full z-10">
                      已领养
                    </div>
                  )}
                  
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFavorite(pet.id);
                    }}
                    className={`absolute top-2 right-2 w-8 h-8 ${pet.isAdopted ? 'bg-white/30 cursor-not-allowed' : 'bg-white/80 backdrop-blur-md hover:bg-white cursor-pointer'} rounded-full flex items-center justify-center transition-colors`}
                    disabled={pet.isAdopted}
                    title={pet.isAdopted ? '已被领养' : ''}
                  >
                    <span className="material-symbols-outlined text-lg text-red-500 filled">
                      favorite
                    </span>
                  </button>
                </div>
                <h4 className="text-base font-bold text-text-main dark:text-text-main-dark truncate">{pet.name}</h4>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-gray-500 dark:text-gray-400">{pet.breed}</span>
                  <span className="text-xs font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-md">{pet.age}</span>
                </div>
                <div className="flex items-center mt-3 text-gray-400 dark:text-gray-500">
                  <span className="material-symbols-outlined text-sm mr-1">location_on</span>
                  <span className="text-xs truncate">{pet.distance}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center pt-20 text-gray-400 dark:text-gray-500">
            <div className="w-20 h-20 bg-gray-100 dark:bg-card-dark rounded-full flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-4xl">favorite_border</span>
            </div>
            <p className="text-lg font-medium">还没有收藏的宠物</p>
            <p className="text-sm mt-2">快去首页看看吧！</p>
            <button 
              onClick={() => navigate('/')}
              className="mt-6 px-6 py-2 bg-primary text-text-main font-bold rounded-xl shadow-sm hover:opacity-90 transition-opacity"
            >
              去逛逛
            </button>
          </div>
        )}
      </main>

      <BottomNav />
    </div>
  );
};

export default Favorites;