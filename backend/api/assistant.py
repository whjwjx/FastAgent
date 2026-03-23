from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import zoneinfo

from core.config import settings
from api.deps import get_current_user
from database.session import get_db
from models.models import User
from services.agent_tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)

router = APIRouter()

class AssistantRequest(BaseModel):
    message: str
    timezone: str = "UTC"
    history: list = [] # List of previous messages {"role": "...", "content": "..."}

def get_openai_client() -> OpenAI:
    api_key = settings.LLM_API_KEY or os.environ.get("LLM_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM_API_KEY is not configured")
    
    return OpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=api_key
    )

@router.post("/stream")
def ask_assistant_stream(
    request: AssistantRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    client = get_openai_client()
    
    try:
        user_tz = zoneinfo.ZoneInfo(request.timezone)
    except Exception:
        user_tz = timezone.utc
    
    now = datetime.now(user_tz)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_str = weekdays[now.weekday()]
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    system_prompt = f"""你是个人AI助手，负责处理用户的聊天、记录想法、管理日程。
当前时间是: {current_time}，今天是{weekday_str}。
请分析用户的意图，调用相应的工具处理想法（增删改查）和日程（增删改查）。
在处理与日期相关的时间词（如“明天”、“本周二”、“下周三”等）时，请务必以“当前时间”和“今天星期几”为基准进行准确的日期推算。
如果指令信息不全（如日程缺少时间），请追问用户。
如果执行了工具，请根据工具的返回结果，用自然、亲切的语言回复用户。"""

    logger.info(f"[User ID: {current_user.id}] New stream request: '{request.message}' (TZ: {request.timezone})")

    def generate():
        routed_model = settings.get_routing_model(request.message)
        logger.info(f"[User ID: {current_user.id}] Routed to model: {routed_model}")
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 加上下文历史记录
        if hasattr(request, 'history') and request.history:
            messages.extend(request.history)
            
        messages.append({"role": "user", "content": request.message})
        
        try:
            # 第一轮调用：大模型决定是否调用工具
            response = client.chat.completions.create(
                model=routed_model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                stream=False  # 第一轮不流式，方便完整获取工具调用
            )
            
            response_message = response.choices[0].message
            
            # 如果没有工具调用，直接流式输出
            if not response_message.tool_calls:
                if response_message.content:
                    yield f"data: {json.dumps({'text': response_message.content}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return

            # 如果有工具调用，执行工具并将结果加回对话上下文
            # 兼容 pydantic 模型转换为字典，处理可能不支持直接序列化的对象
            messages.append(response_message.model_dump(exclude_none=True))
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    function_args = {}
                    
                logger.info(f"[User ID: {current_user.id}] Executing tool: {function_name} with args: {function_args}")
                
                # 执行工具
                result = execute_tool(function_name, db, current_user, user_tz=user_tz, **function_args)
                
                # 将工具执行结果添加到消息列表
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })

            # 第二轮调用：把工具结果给大模型，让它生成最终的自然语言回复（流式）
            stream = client.chat.completions.create(
                model=routed_model,
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'text': delta.content}, ensure_ascii=False)}\n\n"
                    
            # 发送结束标记给前端
            yield "data: [DONE]\n\n"
                    
        except Exception as e:
            logger.error(f"[User ID: {current_user.id}] Error in generate: {str(e)}")
            yield f"data: {json.dumps({'text': '抱歉，处理您的请求时出现了内部错误，请稍后再试。'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
