import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { CATEGORIES } from '../constants';
import BottomNav from '../components/BottomNav';
import { useApp } from '../context/AppContext';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeCategory, setActiveCategory] = useState('all');
  const { pets, toggleFavorite, isFavorite, isLoading, user } = useApp();

  const filteredPets = activeCategory === 'all'
    ? pets
    : pets.filter(pet => pet.category === activeCategory);

  return (
    <div className="relative flex h-full w-full max-w-md mx-auto flex-col min-h-screen overflow-hidden bg-background-light dark:bg-background-dark shadow-2xl">
      {/* Header */}
      <header className="flex items-center justify-between p-4 sticky top-0 z-10 bg-background-light/95 dark:bg-background-dark/95 backdrop-blur-sm">
        <button className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors">
          <span className="material-symbols-outlined text-text-main dark:text-text-main-dark text-2xl">menu</span>
        </button>
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-3xl filled">pets</span>
          <h1 className="text-xl font-extrabold tracking-tight text-text-main dark:text-text-main-dark">PawPal</h1>
        </div>
        <div className="flex w-10 h-10"></div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto no-scrollbar pb-24">
        {/* Hero Text */}
        <div className="px-5 pt-2 pb-6">
          <h2 className="text-3xl font-bold leading-tight text-text-main dark:text-text-main-dark">
            今天就寻找你的<br /><span className="text-secondary dark:text-primary">新伙伴！</span>
          </h2>
        </div>

        {/* Search Bar */}
        <div className="px-5 mb-6">
          <label className="flex w-full items-center rounded-2xl bg-input-bg dark:bg-input-bg-dark h-14 px-4 shadow-sm focus-within:ring-2 focus-within:ring-primary transition-all">
            <span className="material-symbols-outlined text-text-muted text-2xl mr-3">search</span>
            <input
              className="w-full bg-transparent border-none text-base text-text-main dark:text-text-main-dark placeholder-text-muted focus:ring-0 p-0 font-medium focus:outline-none"
              placeholder="搜索名字或品种"
              type="text"
            />
            <button className="p-1.5 bg-white dark:bg-card-dark rounded-xl shadow-sm ml-2">
              <span className="material-symbols-outlined text-primary text-xl">tune</span>
            </button>
          </label>
        </div>

        {/* Categories */}
        <div className="mb-8">
          <div className="flex items-center justify-between px-5 mb-4">
            <h3 className="text-lg font-bold text-text-main dark:text-text-main-dark">分类</h3>
            {/* Removed View All button */}
          </div>
          <div className="flex gap-4 px-5 overflow-x-auto no-scrollbar pb-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                className="flex flex-col items-center gap-2 shrink-0 group"
                onClick={() => setActiveCategory(cat.id)}
              >
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-transform transform group-active:scale-95 ${activeCategory === cat.id
                  ? 'bg-primary shadow-lg shadow-primary/20'
                  : 'bg-white dark:bg-card-dark border border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800'
                  }`}>
                  {cat.isIcon ? (
                    <span className={`material-symbols-outlined text-3xl ${activeCategory === cat.id ? 'text-white' : 'text-gray-400'}`}>
                      {cat.icon}
                    </span>
                  ) : (
                    <img src={cat.image} alt={`${cat.name} icon`} className="w-11 h-11 object-contain drop-shadow-sm" />
                  )}
                </div>
                <span className={`text-sm font-medium ${activeCategory === cat.id ? 'text-text-main font-bold' : 'text-gray-500 dark:text-gray-400'}`}>
                  {cat.name}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="px-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-text-main dark:text-text-main-dark">
              {activeCategory === 'all' ? '为你推荐' : `发现${CATEGORIES.find(c => c.id === activeCategory)?.name || '宠物'}`}
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-4 pb-4">
            {isLoading ? (
              // Skeleton Loading
              Array.from({ length: 4 }).map((_, idx) => (
                <div key={idx} className="bg-card-light dark:bg-card-dark p-3 rounded-2xl shadow-sm animate-pulse">
                  <div className="h-40 w-full rounded-xl bg-gray-200 dark:bg-gray-700 mb-3"></div>
                  <div className="h-5 w-2/3 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                  <div className="flex justify-between">
                    <div className="h-4 w-1/4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-4 w-1/4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  </div>
                </div>
              ))
            ) : filteredPets.length > 0 ? (
              filteredPets.map((pet) => {
                const isFav = isFavorite(pet.id);
                return (
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
                        className={`absolute top-2 right-2 w-8 h-8 ${(!user || pet.isAdopted) ? 'bg-white/10 cursor-not-allowed' : 'bg-white/30 backdrop-blur-md hover:bg-white/50 cursor-pointer'} rounded-full flex items-center justify-center transition-colors z-20`}
                        disabled={!user || pet.isAdopted}
                        title={!user ? '请先登录' : pet.isAdopted ? '已被领养' : ''}
                      >
                        <span className={`material-symbols-outlined text-lg ${isFav ? 'text-red-500 filled' : 'text-white'}`}>
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
                );
              })
            ) : (
              <div className="col-span-2 text-center py-10 text-gray-400">
                <span className="material-symbols-outlined text-4xl mb-2">pets</span>
                <p>该分类下暂无宠物</p>
              </div>
            )}
          </div>
        </div>
      </main>

      <BottomNav />
    </div>
  );
};

export default Home;