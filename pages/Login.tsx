import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';

const Login: React.FC = () => {
    const navigate = useNavigate();
    const { login } = useApp();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            const data = await api.login({ email, password });
            login(data.access_token, data.user);
            navigate('/');
        } catch (err: any) {
            setError(err.message || 'Login failed');
        }
    };

    return (
        <div className="flex flex-col h-screen bg-background-light dark:bg-background-dark max-w-md mx-auto p-4 justify-center">
            <h1 className="text-3xl font-bold text-text-main dark:text-text-main-dark mb-8 text-center">欢迎回来</h1>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
                {error && <p className="text-red-500 text-sm">{error}</p>}
                <button type="submit" className="bg-primary text-[#0f2906] p-4 rounded-xl font-bold text-lg hover:opacity-90 transition-opacity">
                    登录
                </button>
            </form>
            <div className="mt-4 text-center">
                <p className="text-text-muted dark:text-text-muted">还没有账号？ <Link to="/register" className="text-primary font-bold">立即注册</Link></p>
            </div>
            <div className="mt-4 text-center">
                <Link to="/" className="text-text-muted dark:text-text-muted text-sm">返回首页</Link>
            </div>
        </div>
    );
};

export default Login;
