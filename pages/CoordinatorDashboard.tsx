import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';

const CoordinatorDashboard: React.FC = () => {
    const navigate = useNavigate();
    const { user, receivedApplications, refreshReceivedApplications, notifications, refreshNotifications } = useApp();
    const [loading, setLoading] = useState(true);
    const [showNotifications, setShowNotifications] = useState(false);

    useEffect(() => {
    if (user) {
        // 使用AppContext中的receivedApplications状态
        setLoading(false);
        
        // 立即刷新一次
        refreshReceivedApplications().catch(console.error);
        
        // 添加轮询，每10秒刷新一次收到的申请
        const interval = setInterval(() => {
            refreshReceivedApplications().catch(console.error);
        }, 10000);
        
        return () => clearInterval(interval);
        }
    }, [user, receivedApplications, refreshReceivedApplications]);

    const handleUpdateStatus = async (appId: string, newStatus: string) => {
        try {
            await api.updateApplicationStatus(appId, newStatus);
            // 使用AppContext中的refreshReceivedApplications函数
            await refreshReceivedApplications();
            alert(newStatus === 'approved' ? '已批准领养申请' : '已拒绝领养申请');
        } catch (e) {
            console.error(e);
            alert('操作失败');
        }
    };

    return (
        <div className="flex h-full min-h-screen w-full flex-col bg-background-light dark:bg-background-dark max-w-md mx-auto">
            <header className="flex items-center p-4 sticky top-0 z-10 bg-background-light dark:bg-background-dark border-b border-gray-100 dark:border-gray-800">
                <button onClick={() => navigate(-1)} className="text-text-main dark:text-white mr-4">
                    <span className="material-symbols-outlined">arrow_back</span>
                </button>
                <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold">收到的申请</h2>
                </div>
            </header>

            <main className="flex-1 p-4 overflow-y-auto">
                {loading ? (
                    <div className="flex justify-center p-10 text-gray-400">加载中...</div>
                ) : receivedApplications.length === 0 ? (
                    <div className="flex flex-col items-center justify-center p-10 text-gray-400">
                        <span className="material-symbols-outlined text-5xl mb-2">assignment_ind</span>
                        <p>暂无收到的申请</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {receivedApplications.map((app) => (
                            <div key={app.id} className="bg-card-light dark:bg-card-dark p-4 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-800">
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                                        <span className="material-symbols-outlined">person</span>
                                    </div>
                                    <div className="flex-1">
                                        <h4 className="font-bold">{app.full_name}</h4>
                                        <p className="text-xs text-gray-500">申请领养: {app.pet?.name}</p>
                                    </div>
                                    <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${app.status === 'approved' ? 'bg-green-100 text-green-600' :
                                        app.status === 'rejected' ? 'bg-red-100 text-red-600' :
                                            'bg-yellow-100 text-yellow-600'
                                        }`}>
                                        {app.status}
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-2 text-xs mb-4 p-3 bg-gray-50 dark:bg-white/5 rounded-xl">
                                    <p><span className="text-gray-400">电话：</span>{app.phone}</p>
                                    <p><span className="text-gray-400">职业：</span>{app.occupation}</p>
                                    <p className="col-span-2"><span className="text-gray-400">理由：</span>{app.reason}</p>
                                </div>

                                {app.status === 'pending' && (
                                    <div className="flex gap-3">
                                        <button
                                            onClick={() => handleUpdateStatus(app.id, 'approved')}
                                            className="flex-1 bg-primary text-[#0f2906] py-2.5 rounded-xl font-bold text-sm"
                                        >
                                            通过
                                        </button>
                                        <button
                                            onClick={() => handleUpdateStatus(app.id, 'rejected')}
                                            className="flex-1 bg-red-100 text-red-600 py-2.5 rounded-xl font-bold text-sm"
                                        >
                                            拒绝
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
};

export default CoordinatorDashboard;