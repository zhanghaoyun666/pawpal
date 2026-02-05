# PawPal 快速启动指南

## ✅ 已完成
- [x] 数据库迁移（pgvector + 20维画像表）
- [x] 后端代码（AI 功能 + Embedding 本地部署）
- [x] 前端代码（页面 + 组件）

## 🚀 启动前检查清单

### 1. 后端环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 填入以下配置：
```

**必须配置：**
```env
# Supabase（你的项目信息）
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# JWT 密钥（随便填一个长字符串）
SECRET_KEY=your-secret-key-at-least-32-characters-long

# AI 模型（二选一）
## 选项A：美团 LongCat
AI_PROVIDER=longcat
LONGCAT_API_KEY=your-longcat-key
LONGCAT_BASE_URL=https://api.ai.meituan.com/v1

## 选项B：OpenAI
# AI_PROVIDER=openai
# OPENAI_API_KEY=sk-your-openai-key

# Embedding（本地部署，无需修改）
EMBEDDING_MODE=local
EMBEDDING_MODEL_NAME=BAAI/bge-large-zh-v1.5
```

### 2. 安装后端依赖

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 下载 Embedding 模型（首次）

```bash
cd backend

# 自动下载 BGE-large-zh 模型（约 1.2GB）
python download_models.py

# 如果下载慢，使用镜像：
# set HF_ENDPOINT=https://hf-mirror.com  (Windows)
# export HF_ENDPOINT=https://hf-mirror.com  (Mac/Linux)
# python download_models.py
```

### 4. 前端环境变量

```bash
# 在项目根目录（backend 的上一级）
# 确保 .env.local 已存在且配置正确：

cat .env.local
```

内容应该是：
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/chat
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### 5. 安装前端依赖

```bash
# 在项目根目录
npm install
```

## ▶️ 启动应用

### 方式一：手动启动（开发）

**终端 1 - 启动后端：**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**终端 2 - 启动前端：**
```bash
# 在项目根目录
npm run dev
```

访问：http://localhost:5173

### 方式二：使用 concurrently（同时启动）

```bash
# 在项目根目录
npm install -g concurrently

# 添加启动脚本到 package.json
```

在 `package.json` 的 `scripts` 中添加：
```json
"dev:all": "concurrently \"cd backend && uvicorn app.main:app --reload --port 8000\" \"npm run dev\""
```

然后运行：
```bash
npm run dev:all
```

## 🧪 验证安装

### 1. 后端健康检查
```bash
curl http://localhost:8000/
# 应该返回 API 信息

curl http://localhost:8000/api/ai/v2/health
# 应该返回 AI 服务状态
```

### 2. 前端访问
打开浏览器访问 http://localhost:5173

### 3. 测试 AI 功能
- 进入 "/ai-questionnaire" 测试智能问卷
- 完成问卷后查看推荐
- 申请宠物时测试预审功能

## 🔧 常见问题

### 问题1：后端启动失败 `ModuleNotFoundError`
```bash
# 确保在虚拟环境中
pip install -r requirements.txt
```

### 问题2：Embedding 模型下载失败
```bash
# 设置镜像源
set HF_ENDPOINT=https://hf-mirror.com  # Windows
python download_models.py
```

### 问题3：`pgvector` 扩展错误
```sql
-- 在 Supabase SQL Editor 中执行：
CREATE EXTENSION IF NOT EXISTS vector;
```

### 问题4：AI 接口返回 500 错误
- 检查 AI API Key 是否正确
- 检查网络连接（能否访问 LongCat/OpenAI）
- 查看后端日志：`uvicorn app.main:app --log-level debug`

### 问题5：前端无法连接后端
- 检查 `.env.local` 中的 `VITE_API_BASE_URL`
- 确保后端运行在 8000 端口
- 检查防火墙/代理设置

## 📋 启动后检查项

- [ ] 首页显示宠物列表
- [ ] 可以进入 AI 问卷页面
- [ ] 问卷对话正常进行
- [ ] 能看到 AI 推荐结果
- [ ] 可以申请领养
- [ ] 预审对话正常运行
- [ ] 实时聊天功能正常（可选）

## 🎉 完成！

如果所有检查项都通过，恭喜你！PawPal AI 领养平台已成功运行。

遇到其他问题？检查后端日志：
```bash
cd backend
uvicorn app.main:app --reload --port 8000 --log-level debug
```
