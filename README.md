
3. # PawPal - 宠物领养平台
   
   一个基于React + FastAPI的宠物领养平台。
   
   ## 功能特性
   
   - 宠物浏览和搜索
   - 用户注册和登录
   - 宠物收藏功能
   - 领养申请系统
   - 实时聊天功能
   - 协调员管理界面
   
   ## 技术栈
   
   ### 前端
   - React + TypeScript
   - Tailwind CSS
   - React Router
   
   ### 后端
   - FastAPI (Python)
   - Supabase (数据库)
   - JWT认证
   
   ## 安装和运行
   
   ### 后端
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
   
   ### 前端
   ```bash
   npm install
   npm start
   ```
   
   ## 环境配置
   
   参考`.env.example`文件配置环境变量。
