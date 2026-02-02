import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface FAQItem {
    question: string;
    answer: string;
}

const FAQ_DATA: FAQItem[] = [
    {
        question: "如何领养一只宠物？",
        answer: "在首页选择您喜欢的宠物，点击进入详情页，然后点击下方的“申请领养”按钮。按照指引填写真实的个人信息并提交申请即可。送养人收到申请后会通过站内信与您沟通。"
    },
    {
        question: "领养申请提交后，接下来该做什么？",
        answer: "申请提交后，送养人（或协调员）会审阅您的资料。您可以在“个人中心 > 领养记录”中查看实时状态。同时，请留意底栏“消息”图标上的红点提醒，送养人可能会通过聊天向您询问更多细节。"
    },
    {
        question: "我可以删除未完成的领养申请吗？",
        answer: "可以。在“领养记录”页面，对于“审核中”或“被拒绝”的申请，您可以点击右侧的垃圾桶图标进行删除。已经“已成功”的申请无法删除，以保留领养档案。"
    },
    {
        question: "领养后怎么联系送养人？",
        answer: "一旦您提交了申请，系统会自动为您和送养人建立一个专属聊天频道。您可以在“消息”列表中找到对应的对话并开始沟通。"
    },
    {
        question: "为什么我收不到新消息提醒？",
        answer: "PawPal 提供了即时的未读状态提示。如果有新消息，您的底栏“消息”图标会出现呼吸灯效果的小红点。为了获得最佳体验，请确保网络连接正常并保持应用处于非静默状态。"
    },
    {
        question: "我想送养宠物，应该如何发布？",
        answer: "如果您是具有权限的协调员，可以在“个人中心”直接看到“发布送养信息”的绿色按钮。点击后即可填报宠物的各项资料。此外，您也可以在“我的发布”页面中找到发布入口。"
    }
];

const HelpCenter: React.FC = () => {
    const navigate = useNavigate();
    const [activeIndex, setActiveIndex] = useState<number | null>(null);

    return (
        <div className="flex h-full min-h-screen w-full flex-col bg-background-light dark:bg-background-dark max-w-md mx-auto">
            <header className="flex items-center p-4 sticky top-0 z-10 bg-background-light dark:bg-background-dark border-b border-gray-100 dark:border-gray-800">
                <button onClick={() => navigate(-1)} className="text-text-main dark:text-white mr-4">
                    <span className="material-symbols-outlined">arrow_back</span>
                </button>
                <h2 className="text-lg font-bold">帮助中心</h2>
            </header>

            <main className="flex-1 p-5 space-y-4">
                <div className="mb-6 text-center">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-3">
                        <span className="material-symbols-outlined text-primary text-3xl">live_help</span>
                    </div>
                    <h3 className="text-xl font-bold text-text-main dark:text-white">常见问题解答</h3>
                    <p className="text-sm text-gray-400 mt-1">为您解决领养过程中的各类困惑</p>
                </div>

                <div className="space-y-3">
                    {FAQ_DATA.map((item, index) => (
                        <div
                            key={index}
                            className={`bg-card-light dark:bg-card-dark rounded-2xl border transition-all ${activeIndex === index
                                ? 'border-primary shadow-sm'
                                : 'border-gray-100 dark:border-gray-800'
                                }`}
                        >
                            <button
                                onClick={() => setActiveIndex(activeIndex === index ? null : index)}
                                className="w-full flex items-center justify-between p-4 text-left"
                            >
                                <span className="font-bold text-sm text-text-main dark:text-white flex-1 pr-4">
                                    {item.question}
                                </span>
                                <span className={`material-symbols-outlined text-gray-400 transition-transform ${activeIndex === index ? 'rotate-180 text-primary' : ''}`}>
                                    expand_more
                                </span>
                            </button>
                            {activeIndex === index && (
                                <div className="px-4 pb-4 animate-in fade-in slide-in-from-top-1 duration-200">
                                    <div className="h-px bg-gray-50 dark:bg-gray-800 mb-3"></div>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed font-normal">
                                        {item.answer}
                                    </p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                <div className="mt-8 p-5 bg-card-light dark:bg-card-dark rounded-3xl border border-dashed border-gray-100 dark:border-gray-800 text-center">
                    <p className="text-sm text-gray-400 mb-3">还有其他问题？</p>
                    <button className="px-6 py-2 bg-primary text-[#0f2906] rounded-xl font-bold text-sm shadow-sm hover:opacity-90">
                        联系人工客服
                    </button>
                </div>
            </main>
        </div>
    );
};

export default HelpCenter;
