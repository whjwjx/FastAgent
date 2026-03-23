from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置全局日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from database.session import engine
from models import models
from api import auth, thoughts, chat, assistant, schedules

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAIStack MVP", description="个人AI助手（多用户版） API", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(thoughts.router, prefix="/api/thoughts", tags=["thoughts"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(assistant.router, prefix="/api/assistant", tags=["assistant"])

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAIStack Backend MVP API"}
