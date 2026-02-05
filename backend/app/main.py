from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PawPal API", description="Backend for PawPal Adoption App")

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import pets, users, chats, applications, auth, websocket as ws_router
from app.routers import sse as sse_router
from app.routers import ai as ai_router
from app.routers import ai_v2 as ai_v2_router  # 新的 AI V2 路由
from app.routers.chats import set_sse_manager

# 设置 SSE 管理器到 chats 模块
set_sse_manager(sse_router.sse_manager)

app.include_router(pets.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(applications.router)
app.include_router(auth.router)
# WebSocket 路由（Vercel 不支持，但保留用于其他部署环境）
app.include_router(ws_router.router)
# SSE 路由（Vercel 支持）
app.include_router(sse_router.router)
# AI 功能路由（旧版本，兼容）
app.include_router(ai_router.router)
# AI 功能路由 V2（新实现，对齐 PRD）
app.include_router(ai_v2_router.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to PawPal API",
        "version": "2.0",
        "features": [
            "websocket",
            "sse",
            "ai_questionnaire",
            "ai_matching_v2",
            "ai_precheck_v2"
        ],
        "endpoints": {
            "websocket": "/ws/chat",
            "sse": "/api/sse/connect?user_id=xxx",
            "ai_v1": "/api/ai",
            "ai_v2": "/api/ai/v2"
        }
    }
