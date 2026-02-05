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

@app.get("/")
def read_root():
    return {
        "message": "Welcome to PawPal API",
        "websocket": "/ws/chat",
        "sse": "/api/sse/connect?user_id=xxx"
    }
