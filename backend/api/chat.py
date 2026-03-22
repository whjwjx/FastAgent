from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.session import get_db
from models.models import User, Thought, Schedule
from api.deps import get_current_user

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    action_type: str = "chat"
    data: dict = {}

@router.post("/", response_model=ChatResponse)
def chat_with_agent(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Simple Mock Agent Hub for MVP
    # In real implementation, this would call LLM (e.g., OpenAI) to parse intent
    message = request.message.lower()
    
    if "想法" in message or "记录" in message:
        # Mock Thought Agent
        content = request.message.replace("帮我记录一个想法：", "").replace("记录想法", "").strip()
        new_thought = Thought(content=content, user_id=current_user.id)
        db.add(new_thought)
        db.commit()
        db.refresh(new_thought)
        return ChatResponse(
            reply=f"已成功记录您的想法：{content}",
            action_type="thought",
            data={"id": new_thought.id, "content": new_thought.content}
        )
        
    elif "日程" in message or "安排" in message:
        # Mock Schedule Agent (just a placeholder logic)
        return ChatResponse(
            reply="已识别到日程意图，即将为您安排日程（功能开发中...）",
            action_type="schedule",
            data={}
        )
    
    # Default chat
    return ChatResponse(
        reply=f"AI助手收到您的消息：{request.message}",
        action_type="chat",
        data={}
    )
