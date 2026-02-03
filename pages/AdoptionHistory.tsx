import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';

const AdoptionHistory: React.FC = () => {
    const navigate = useNavigate();
    const { user, applications, isLoading, refreshApplications } = useApp();

    const handleDelete = async (appId: string, status: string) => {
        if (!user) return;
        if (status === 'approved') {
            alert('已完成的领养记录不能删除');
            return;
        }

        if (!window.confirm('确定要删除这条领养记录吗？')) return;

        try {
            await api.deleteApplication(appId, user.id);
            await refreshApplications();
            alert('记录已成功删除');
        } catch (e: any) {
            console.error(e);
            alert(e.message || '删除失败');
        }
    };

    // 获取宠物详情函数
    const handleViewPet = async (petId: string) => {
        if (!petId) return;
        navigate(`/details/${petId}`);
    };

    return (
        <div className="flex h-full min-h-screen w-full flex-col bg-background-light dark:bg-background-dark max-w-md mx-auto">
            <header className="flex items-center p-4 sticky top-0 z-10 bg-background-light dark:bg-background-dark border-b border-gray-100 dark:border-gray-800">
                <button onClick={() => navigate(-1)} className="text-text-main dark:text-white mr-4">
                    <span className="material-symbols-outlined">arrow_back</span>
                </button>
                <h2 className="text-lg font-bold">领养记录</h2>
            </header>

            <main className="flex-1 p-4 overflow-y-auto">
                {isLoading ? (
                    <div className="flex justify-center p-10 text-gray-400">加载中...</div>
                ) : applications.length === 0 ? (
                    <div className="flex flex-col items-center justify-center p-10 text-gray-400">
                        <span className="material-symbols-outlined text-5xl mb-2">history</span>
                        <p>暂无领养记录</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {applications.map((app) => (
                            <div key={app.id} className="bg-card-light dark:bg-card-dark p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800">
                                <div className="flex items-center gap-4 mb-3">
                                    <div 
                                        className="w-16 h-16 rounded-xl bg-gray-200 bg-cover bg-center cursor-pointer hover:opacity-80 transition-opacity" 
                                        style={{ backgroundImage: `url(${app.pet?.image})` }}
                                        onClick={() => handleViewPet(app.pet_id)}
                                        title="查看宠物详情"
                                    ></div>
                                    <div className="flex-1">
                                        <div className="flex justify-between items-start">
                                            <h4 
                                                className="font-bold text-lg cursor-pointer hover:text-primary transition-colors" 
                                                onClick={() => handleViewPet(app.pet_id)}
                                                title="查看宠物详情"
                                            >
                                                {app.pet?.name}
                                            </h4>
                                            {app.status !== 'approved' && (
                                                <button
                                                    onClick={() => handleDelete(app.id, app.status)}
                                                    className="text-gray-400 hover:text-red-500 transition-colors"
                                                    title="删除申请"
                                                >
                                                    <span className="material-symbols-outlined text-xl">delete</span>
                                                </button>
                                            )}
                                        </div>
                                        <p className="text-sm text-gray-500">{new Date(app.created_at).toLocaleDateString()}</p>
                                    </div>
                                    <div className={`px-3 py-1 rounded-full text-xs font-bold ${app.status === 'approved' ? 'bg-green-100 text-green-600' :
                                        app.status === 'rejected' ? 'bg-red-100 text-red-600' :
                                            'bg-yellow-100 text-yellow-600'
                                        }`}>
                                        {app.status === 'approved' ? '已成功' : app.status === 'rejected' ? '被拒绝' : '审核中'}
                                    </div>
                                </div>
                                <div className="text-sm text-gray-600 dark:text-gray-400 border-t border-gray-50 dark:border-gray-800 pt-3">
                                    <p>申请人：{app.full_name}</p>
                                    <p>备注：{app.reason || '无'}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
};

export default AdoptionHistory;