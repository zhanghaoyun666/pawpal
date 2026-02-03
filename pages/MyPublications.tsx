import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { Pet } from '../types';

const MyPublications: React.FC = () => {
    const navigate = useNavigate();
    const { user, refreshMyPets } = useApp();
    const [pets, setPets] = useState<Pet[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user) {
            console.log('Fetching pets for owner_id:', user.id);
            refreshMyPets()
                .then(data => {
                    console.log('Fetched pets:', data);
                    setPets(data);
                })
                .catch(console.error)
                .finally(() => setLoading(false));
        }
    }, [user, refreshMyPets]);

    const handleDelete = async (petId: string, petName: string, isAdopted: boolean) => {
        if (isAdopted) {
            alert('已领养的宠物无法下架');
            return;
        }
        
        if (window.confirm(`确定要下架宠物"${petName}"吗？`)) {
            try {
                await api.deletePet(petId);
                setPets(prev => prev.filter(p => p.id !== petId));
                alert('下架成功');
            } catch (error: any) {
                console.error(error);
                alert('下架失败：' + (error.message || '未知错误'));
            }
        }
    };

    return (
        <div className="flex h-full min-h-screen w-full flex-col bg-background-light dark:bg-background-dark max-w-md mx-auto">
            <header className="flex items-center p-4 sticky top-0 z-10 bg-background-light dark:bg-background-dark border-b border-gray-100 dark:border-gray-800">
                <button onClick={() => navigate(-1)} className="text-text-main dark:text-white mr-4">
                    <span className="material-symbols-outlined">arrow_back</span>
                </button>
                <h2 className="text-lg font-bold">我的发布</h2>
            </header>

            <main className="flex-1 p-4 overflow-y-auto">
                {loading ? (
                    <div className="flex justify-center p-10 text-gray-400">加载中...</div>
                ) : pets.length === 0 ? (
                    <div className="flex flex-col items-center justify-center p-10 text-gray-400">
                        <span className="material-symbols-outlined text-5xl mb-2">pets</span>
                        <p>暂无已发布的宠物</p>
                        <button
                            onClick={() => navigate('/add-pet')}
                            className="mt-4 bg-primary text-[#0f2906] px-6 py-2 rounded-xl font-bold"
                        >
                            立即发布
                        </button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {pets.map((pet) => (
                            <div key={pet.id} className="bg-card-light dark:bg-card-dark p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800 flex items-center gap-4">
                                <div className="w-20 h-20 rounded-xl bg-gray-200 bg-cover bg-center relative" style={{ backgroundImage: `url(${pet.image})` }}>
                                    {pet.isAdopted && (
                                        <div className="absolute inset-0 bg-black/50 rounded-xl flex items-center justify-center">
                                            <span className="text-white text-xs font-bold">已领养</span>
                                        </div>
                                    )}
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                        <h4 className="font-bold text-lg">{pet.name}</h4>
                                        <span className={`text-xs px-2 py-0.5 rounded-full ${pet.isAdopted ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' : 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'}`}>
                                            {pet.isAdopted ? '已领养' : '未领养'}
                                        </span>
                                    </div>
                                    <div className="flex gap-2 mt-1">
                                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">{pet.breed}</span>
                                        <span className="text-xs bg-gray-100 dark:bg-white/10 text-gray-500 px-2 py-0.5 rounded-full">{pet.category === 'dog' ? '狗狗' : '猫猫'}</span>
                                    </div>
                                    <p className="text-sm text-gray-500 mt-2 flex items-center gap-1">
                                        <span className="material-symbols-outlined text-xs">location_on</span>
                                        {pet.distance}
                                    </p>
                                </div>
                                <div className="flex flex-col gap-2">
                                    <button
                                        onClick={() => navigate(`/details/${pet.id}`)}
                                        className="p-2 text-primary hover:bg-primary/10 rounded-full transition-colors"
                                        title="预览"
                                    >
                                        <span className="material-symbols-outlined">visibility</span>
                                    </button>
                                    <button
                                        onClick={() => handleDelete(pet.id, pet.name, pet.isAdopted || false)}
                                        className={`p-2 rounded-full transition-colors ${pet.isAdopted ? 'text-gray-400 cursor-not-allowed' : 'text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'}`}
                                        title={pet.isAdopted ? "已领养的宠物无法下架" : "下架"}
                                        disabled={pet.isAdopted}
                                    >
                                        <span className="material-symbols-outlined">{pet.isAdopted ? 'lock' : 'delete'}</span>
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
};

export default MyPublications;