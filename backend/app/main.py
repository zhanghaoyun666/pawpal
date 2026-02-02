from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PawPal API", description="Backend for PawPal Adoption App")

origins = [
    "http://localhost:5173", # Vite default
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

from app.routers import pets, users, chats, applications, auth

app.include_router(pets.router)
app.include_router(users.router)
app.include_router(chats.router)
app.include_router(applications.router)
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to PawPal API"}
