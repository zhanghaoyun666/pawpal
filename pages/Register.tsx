import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';

const Register: React.FC = () => {
    const navigate = useNavigate();
    const { login } = useApp();
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('user');
    const [avatarUrl, setAvatarUrl] = useState('https://api.dicebear.com/7.x/avataaars/svg?seed=Felix'); // Default
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            await api.register({ name, email, password, role, avatar_url: avatarUrl });
            // Auto login after register
            const loginData = await api.login({ email, password });
            login(loginData.access_token, loginData.user);
            navigate('/');
        } catch (err: any) {
            setError(err.message || 'Registration failed');
        }
    };

    return (
        <div className="flex flex-col h-screen bg-background-light dark:bg-background-dark max-w-md mx-auto p-4 justify-center">
            <h1 className="text-3xl font-bold text-text-main dark:text-text-main-dark mb-8 text-center">加入 PawPal</h1>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <input
                    type="text"
                    placeholder="完整姓名"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark"
                    required
                />
                <input
                    type="email"
                    placeholder="邮箱"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark"
                    required
                />
                <input
                    type="password"
                    placeholder="密码"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-card-light dark:bg-surface-dark text-text-main dark:text-text-main-dark"
                    required
                />

                <div className="flex gap-4 p-1">
                    <label className="flex items-center gap-2 text-text-main dark:text-text-main-dark cursor-pointer">
                        <input
                            type="radio"
                            name="role"
                            value="user"
                            checked={role === 'user'}
                            onChange={() => setRole('user')}
                        />
                        领养人
                    </label>
                    <label className="flex items-center gap-2 text-text-main dark:text-text-main-dark cursor-pointer">
                        <input
                            type="radio"
                            name="role"
                            value="coordinator"
                            checked={role === 'coordinator'}
                            onChange={() => setRole('coordinator')}
                        />
                        送养人/协调员
                    </label>
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-text-main dark:text-text-main-dark font-medium px-1">选择头像</label>
                    <div className="grid grid-cols-6 gap-2">
                        {[
                            'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix',
                            'https://api.dicebear.com/7.x/avataaars/svg?seed=Aneka',
                            'https://api.dicebear.com/7.x/avataaars/svg?seed=Zoe',
                            'https://api.dicebear.com/7.x/bottts/svg?seed=Buddy',
                            'https://api.dicebear.com/7.x/bottts/svg?seed=Cleo',
                            'https://api.dicebear.com/7.x/adventurer/svg?seed=Max'
                        ].map((url) => (
                            <button
                                key={url}
                                type="button"
                                onClick={() => setAvatarUrl(url)}
                                className={`rounded-full overflow-hidden border-2 transition-all aspect-square ${avatarUrl === url ? 'border-primary ring-2 ring-primary/30 scale-110' : 'border-transparent hover:border-gray-300'}`}
                            >
                                <img src={url} alt="avatar" className="w-full h-full object-cover" />
                            </button>
                        ))}
                    </div>
                </div>

                {error && <p className="text-red-500 text-sm">{error}</p>}
                <button type="submit" className="bg-primary text-[#0f2906] p-4 rounded-xl font-bold text-lg hover:opacity-90 transition-opacity">
                    创建账号
                </button>
            </form>
            <div className="mt-4 text-center">
                <p className="text-text-muted dark:text-text-muted">已经有账号了？ <Link to="/login" className="text-primary font-bold">立即登录</Link></p>
            </div>
            <div className="mt-4 text-center">
                <Link to="/" className="text-text-muted dark:text-text-muted text-sm">返回首页</Link>
            </div>
        </div>
    );
};

export default Register;
