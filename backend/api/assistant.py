from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os
import json
from openai import OpenAI
from sqlalchemy.orm import Session
from datetime import datetime, date
from core.config import settings
from api.deps import get_current_user
from database.session import get_db
from models.models import User, Thought, Schedule

router = APIRouter()

class AssistantRequest(BaseModel):
    message: str

class AssistantResponse(BaseModel):
    reply: str
    action_taken: str = "chat" # chat, thought, schedule, multiple

def get_openai_client() -> OpenAI:
    api_key = settings.ARK_API_KEY or os.environ.get("ARK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ARK_API_KEY is not configured")
    
    return OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key
    )

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "record_thought",
            "description": "记录用户的想法、笔记或灵感",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_content": {
                        "type": "string",
                        "description": "用户原始的想法内容"
                    },
                    "refined_content": {
                        "type": "string",
                        "description": "AI润色或整理后的想法内容"
                    },
                    "tags": {
                        "type": "string",
                        "description": "相关的标签，逗号分隔，例如：工作,日常,灵感"
                    }
                },
                "required": ["original_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_schedule",
            "description": "创建一个日程、提醒或待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "日程标题"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "开始时间，ISO格式 (YYYY-MM-DDTHH:MM:SS) 或者 YYYY-MM-DD"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "结束时间，ISO格式 (YYYY-MM-DDTHH:MM:SS) 或者 YYYY-MM-DD"
                    },
                    "location": {
                        "type": "string",
                        "description": "地点，如果没有则为空"
                    }
                },
                "required": ["title", "start_time"]
            }
        }
    }
]

@router.post("/", response_model=AssistantResponse)
def ask_assistant(
    request: AssistantRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    client = get_openai_client()
    
    # Context info for the LLM
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_prompt = f"""你是个人AI助手，负责处理用户的聊天、记录想法、管理日程。
当前时间是: {current_time}。
请分析用户的意图，如果用户想要记录想法，请调用 record_thought。如果用户想要记录日程，请调用 create_schedule。
如果指令信息不全（如日程缺少时间），请追问用户。如果只是普通的聊天，请直接回复。"""

    try:
        completion = client.chat.completions.create(
            model="doubao-1-5-lite-32k-250115",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message},
            ],
            tools=TOOLS,
            tool_choice="auto"
        )
        
        response_message = completion.choices[0].message
        
        if response_message.tool_calls:
            action_taken = "multiple" if len(response_message.tool_calls) > 1 else ""
            reply_text = "我已经为您执行了以下操作：\n"
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "record_thought":
                    if not action_taken: action_taken = "thought"
                    thought = Thought(
                        user_id=current_user.id,
                        original_content=function_args.get("original_content"),
                        refined_content=function_args.get("refined_content"),
                        tags=function_args.get("tags")
                    )
                    db.add(thought)
                    db.commit()
                    reply_text += f"- 记录想法: {function_args.get('original_content')[:20]}...\n"
                    
                elif function_name == "create_schedule":
                    if not action_taken: action_taken = "schedule"
                    
                    start_time_str = function_args.get("start_time")
                    # Naive parsing for MVP
                    try:
                        start_time = datetime.fromisoformat(start_time_str)
                    except ValueError:
                        # Fallback
                        start_time = datetime.strptime(start_time_str, "%Y-%m-%d") if len(start_time_str) == 10 else datetime.now()
                        
                    end_time = None
                    if function_args.get("end_time"):
                        try:
                            end_time = datetime.fromisoformat(function_args.get("end_time"))
                        except ValueError:
                            pass

                    schedule = Schedule(
                        user_id=current_user.id,
                        title=function_args.get("title"),
                        start_time=start_time,
                        end_time=end_time,
                        location=function_args.get("location")
                    )
                    db.add(schedule)
                    db.commit()
                    reply_text += f"- 创建日程: {function_args.get('title')} ({start_time_str})\n"
                    
            return AssistantResponse(reply=reply_text, action_taken=action_taken)
            
        else:
            return AssistantResponse(reply=response_message.content, action_taken="chat")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
