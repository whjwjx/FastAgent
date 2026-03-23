from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from datetime import datetime, date, timezone
import zoneinfo
from core.config import settings
from api.deps import get_current_user
from database.session import get_db
from models.models import User, Thought, Schedule

router = APIRouter()

class AssistantRequest(BaseModel):
    message: str
    timezone: str = "UTC"

class AssistantResponse(BaseModel):
    reply: str
    action_taken: str = "chat" # chat, thought, schedule, multiple

def get_openai_client() -> OpenAI:
    api_key = settings.LLM_API_KEY or os.environ.get("LLM_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM_API_KEY is not configured")
    
    return OpenAI(
        base_url=settings.LLM_BASE_URL,
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
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "相关的标签列表，例如：['工作', '日常', '灵感']"
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
请分析用户的意图，如果用户想要记录想法，请调用 record_thought。如果用户想要记录日程，请调用 create_schedule。
在处理与日期相关的时间词（如“明天”、“本周二”、“下周三”等）时，请务必以“当前时间”和“今天星期几”为基准进行准确的日期推算。
如果指令信息不全（如日程缺少时间），请追问用户。如果只是普通的聊天，请直接回复。"""

    logger.info(f"[User ID: {current_user.id}] New stream request: '{request.message}' (TZ: {request.timezone})")

    def generate():
        try:
            routed_model = settings.get_routing_model(request.message)
            logger.info(f"[User ID: {current_user.id}] Routed to model: {routed_model}")
            
            stream = client.chat.completions.create(
                model=routed_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message},
                ],
                tools=TOOLS,
                tool_choice="auto",
                stream=True
            )
            
            tool_calls = []
            
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'text': delta.content}, ensure_ascii=False)}\n\n"
                
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        while len(tool_calls) <= tc.index:
                            tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                        if tc.id:
                            tool_calls[tc.index]["id"] = tc.id
                        if tc.function.name:
                            tool_calls[tc.index]["function"]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

            if tool_calls:
                logger.info(f"[User ID: {current_user.id}] Model triggered {len(tool_calls)} tool calls.")
                reply_text = "\n我已经为您执行了以下操作：\n"
                action_taken = ""
                for tc in tool_calls:
                    function_name = tc["function"]["name"]
                    try:
                        function_args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        logger.error(f"[User ID: {current_user.id}] Failed to decode tool arguments: {tc['function']['arguments']}")
                        continue
                    
                    if function_name == "record_thought":
                        logger.info(f"[User ID: {current_user.id}] Executing tool: record_thought with args: {function_args}")
                        if not action_taken: action_taken = "thought"
                        thought = Thought(
                            user_id=current_user.id,
                            original_content=function_args.get("original_content"),
                            refined_content=function_args.get("refined_content"),
                            tags=function_args.get("tags")
                        )
                        db.add(thought)
                        db.commit()
                        logger.info(f"[User ID: {current_user.id}] Thought recorded successfully. Content preview: {thought.original_content[:20]}...")
                        reply_text += f"- 记录想法: {function_args.get('original_content')[:20]}...\n"
                        
                    elif function_name == "create_schedule":
                        logger.info(f"[User ID: {current_user.id}] Executing tool: create_schedule with args: {function_args}")
                        if not action_taken: action_taken = "schedule"
                        
                        start_time_str = function_args.get("start_time")
                        try:
                            start_time = datetime.fromisoformat(start_time_str)
                            if start_time.tzinfo is None:
                                start_time = start_time.replace(tzinfo=user_tz)
                            start_time = start_time.astimezone(timezone.utc)
                        except ValueError:
                            try:
                                start_time = datetime.strptime(start_time_str, "%Y-%m-%d").replace(tzinfo=user_tz)
                                start_time = start_time.astimezone(timezone.utc)
                            except ValueError:
                                reply_text += f"- 创建日程失败: 无法识别的时间格式 '{start_time_str}'，请提供明确的时间。\n"
                                continue
                            
                        end_time = None
                        if function_args.get("end_time"):
                            try:
                                end_time = datetime.fromisoformat(function_args.get("end_time"))
                                if end_time.tzinfo is None:
                                    end_time = end_time.replace(tzinfo=user_tz)
                                end_time = end_time.astimezone(timezone.utc)
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
                        logger.info(f"[User ID: {current_user.id}] Schedule created successfully: {schedule.title}")
                        reply_text += f"- 创建日程: {function_args.get('title')} ({start_time_str})\n"
                
                logger.info(f"[User ID: {current_user.id}] Stream completed with actions: {action_taken}")
                yield f"data: {json.dumps({'text': reply_text, 'action_taken': action_taken}, ensure_ascii=False)}\n\n"
            else:
                logger.info(f"[User ID: {current_user.id}] Stream completed as chat without tool calls.")
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"[User ID: {current_user.id}] Error in generation stream: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/", response_model=AssistantResponse)
def ask_assistant(
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
请分析用户的意图，如果用户想要记录想法，请调用 record_thought。如果用户想要记录日程，请调用 create_schedule。
在处理与日期相关的时间词（如“明天”、“本周二”、“下周三”等）时，请务必以“当前时间”和“今天星期几”为基准进行准确的日期推算。
如果指令信息不全（如日程缺少时间），请追问用户。如果只是普通的聊天，请直接回复。"""

    logger.info(f"[User ID: {current_user.id}] New standard request: '{request.message}' (TZ: {request.timezone})")

    try:
        routed_model = settings.get_routing_model(request.message)
        logger.info(f"[User ID: {current_user.id}] Routed to model: {routed_model}")
        
        # 将上下文（提示词+工具）发送给LLM，得到答复
        completion = client.chat.completions.create(
            model=routed_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message},
            ],
            tools=TOOLS,
            tool_choice="auto"
        )
        
        response_message = completion.choices[0].message
        
        # 根据回答是否包含工具调用，判断是否需要执行操作
        if response_message.tool_calls:
            logger.info(f"[User ID: {current_user.id}] Model triggered {len(response_message.tool_calls)} tool calls.")
            action_taken = "multiple" if len(response_message.tool_calls) > 1 else ""
            reply_text = "我已经为您执行了以下操作：\n"
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    logger.error(f"[User ID: {current_user.id}] Failed to decode tool arguments: {tool_call.function.arguments}")
                    continue
                
                if function_name == "record_thought":
                    logger.info(f"[User ID: {current_user.id}] Executing tool: record_thought with args: {function_args}")
                    if not action_taken: action_taken = "thought"
                    thought = Thought(
                        user_id=current_user.id,
                        original_content=function_args.get("original_content"),
                        refined_content=function_args.get("refined_content"),
                        tags=function_args.get("tags")
                    )
                    db.add(thought)
                    db.commit()
                    logger.info(f"[User ID: {current_user.id}] Thought recorded successfully. Content preview: {thought.original_content[:20]}...")
                    reply_text += f"- 记录想法: {function_args.get('original_content')[:20]}...\n"
                    
                elif function_name == "create_schedule":
                    logger.info(f"[User ID: {current_user.id}] Executing tool: create_schedule with args: {function_args}")
                    if not action_taken: action_taken = "schedule"
                    
                    start_time_str = function_args.get("start_time")
                    try:
                        start_time = datetime.fromisoformat(start_time_str)
                        if start_time.tzinfo is None:
                            start_time = start_time.replace(tzinfo=user_tz)
                        start_time = start_time.astimezone(timezone.utc)
                    except ValueError:
                        try:
                            start_time = datetime.strptime(start_time_str, "%Y-%m-%d").replace(tzinfo=user_tz)
                            start_time = start_time.astimezone(timezone.utc)
                        except ValueError:
                            # 容错与兜底机制: 提示用户时间格式无法识别
                            reply_text += f"- 创建日程失败: 无法识别的时间格式 '{start_time_str}'，请提供明确的时间（例如：明天下午3点）。\n"
                            continue
                        
                    end_time = None
                    if function_args.get("end_time"):
                        try:
                            end_time = datetime.fromisoformat(function_args.get("end_time"))
                            if end_time.tzinfo is None:
                                end_time = end_time.replace(tzinfo=user_tz)
                            end_time = end_time.astimezone(timezone.utc)
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
                    logger.info(f"[User ID: {current_user.id}] Schedule created successfully: {schedule.title}")
                    reply_text += f"- 创建日程: {function_args.get('title')} ({start_time_str})\n"
                
            logger.info(f"[User ID: {current_user.id}] Request completed with actions: {action_taken}")
            return AssistantResponse(reply=reply_text, action_taken=action_taken)
            
        else:
            logger.info(f"[User ID: {current_user.id}] Request completed as chat without tool calls.")
            return AssistantResponse(reply=response_message.content, action_taken="chat")
            
    except Exception as e:
        logger.error(f"[User ID: {current_user.id}] Error in standard request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
