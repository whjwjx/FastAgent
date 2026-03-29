from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import logging
import uuid
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
    message: str = ""
    timezone: str = "UTC"
    history: list = [] # List of previous messages {"role": "...", "content": "..."}
    
    # For confirmation (Phase 1)
    is_confirmation: bool = False
    action_id: str = None
    tool_calls: list = []
    is_cancelled: bool = False

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
    
    system_prompt = f"""你是一个聪明、博学且高情商的个人AI助手，具备强大的逻辑分析、知识问答和日常交流能力。你可以像一位好朋友一样与用户自然对话、解答问题、提供建议。

【当前环境信息】
当前时间是: {current_time}，今天是{weekday_str}。在处理与日期相关的时间词（如“明天”、“本周二”、“下周三”等）时，请务必以当前时间为基准进行准确推算。

【你的核心职责】
1. **日常交流与问答（首选）**：对于用户的日常聊天、知识请教、建议咨询、逻辑分析等通用问题，请直接运用你的知识库给出详尽、有帮助且自然的回复。
2. **联网搜索（按需获取新知识）**：如果用户询问**最新的新闻、实时资讯**，或者超出了你静态知识库的问题，请调用 `search_web` 工具去互联网获取信息，然后再总结给用户。
3. **个人数据管理（仅在需要时调用工具）**：**仅当**用户明确要求“记录想法/笔记/灵感”或“管理日程/待办事项”（包括增、删、改、查）时，你才应该调用相应的本地数据工具。

【工具调用规则（如果触发）】
- **明确边界**：不要为了调用工具而调用工具。如果用户只是在和你聊天探讨，不要去查询或创建想法/日程。
- **时间推算**：如果用户未提供具体时间，请按以下默认规则处理，并输出完整的ISO时间格式（YYYY-MM-DDTHH:MM:SS）：
  - 未提供具体时间或提及“上午”，默认设为当天 07:00:00
  - 提及“下午”，默认设为当天 13:00:00
  - 提及“晚上”，默认设为当天 18:00:00
- **批量操作**：当需要删除多条数据时，务必使用支持数组参数的删除工具（如传入 [id1, id2]）进行一次性批量操作。
- **信息补全**：如果调用工具所需的关键信息不全（例如完全没提日期或内容），请先追问用户。

请记住，你首先是一个全能的AI助手，其次才是一个可以调用工具管理个人数据的管家。在执行完工具后，请用自然、亲切的语言向用户反馈结果。"""

    logger.info(f"[User ID: {current_user.id}] New stream request: '{request.message}' (TZ: {request.timezone})")

    def generate():
        routed_model = settings.get_routing_model(request.message or "confirm action")
        logger.info(f"[User ID: {current_user.id}] Routed to model: {routed_model}")
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 加上下文历史记录
        if hasattr(request, 'history') and request.history:
            messages.extend(request.history)
            
        if request.is_confirmation:
            if request.is_cancelled:
                messages.append({"role": "system", "content": "系统提示：用户取消了刚才的操作。请直接回复用户已取消。"})
            else:
                results = []
                for tool_call in request.tool_calls:
                    function_name = tool_call.get("function", {}).get("name", "")
                    args = tool_call.get("function", {}).get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            args = {}
                    try:
                        res = execute_tool(function_name, db, current_user, user_tz=user_tz, **args)
                        results.append({"name": function_name, "result": res})
                    except Exception as e:
                        results.append({"name": function_name, "error": str(e)})
                
                # 为了让大模型能正确理解并结束对话，我们需要伪造完整的 function call 历史，而不是仅仅发一个系统提示
                # 构造 Assistant 的 Tool Call 消息
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": request.tool_calls
                })
                # 构造对应的 Tool 返回结果消息
                for i, tool_call in enumerate(request.tool_calls):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", f"call_{i}"),
                        "name": tool_call.get("function", {}).get("name", ""),
                        "content": json.dumps(results[i] if i < len(results) else {"error": "unknown"}, ensure_ascii=False)
                    })
        else:
            messages.append({"role": "user", "content": request.message})
        
        try:
            # 引入原生 Python 的 ReAct 循环，允许大模型在拿到工具结果后再次判断是否继续调用工具
            # 最大循环次数限制，防止死循环
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"[User ID: {current_user.id}] ReAct loop iteration: {iteration}")
                
                # 调用大模型，开启流式以便及时返回中间状态和最终文本
                stream_response = client.chat.completions.create(
                    model=routed_model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    stream=True
                )
                
                tool_calls_accumulator = {}
                has_tool_calls = False
                round_content = ""
                
                for chunk in stream_response:
                    delta = chunk.choices[0].delta
                    
                    if delta.content:
                        round_content += delta.content
                        # 向前端下发普通文本气泡
                        yield f"data: {json.dumps({'type': 'text', 'text': delta.content}, ensure_ascii=False)}\n\n"
                        
                    if delta.tool_calls:
                        has_tool_calls = True
                        for tc in delta.tool_calls:
                            index = tc.index
                            if index not in tool_calls_accumulator:
                                tool_calls_accumulator[index] = {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            
                            if tc.id:
                                tool_calls_accumulator[index]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_accumulator[index]["function"]["name"] += tc.function.name
                                    # 当解析到工具名称时，下发中间状态作为独立的工具气泡
                                    func_name = tool_calls_accumulator[index]["function"]["name"]
                                    
                                    # 简单映射一下给前端展示的友好名称
                                    tool_name_mapping = {
                                        "search_web": "联网搜索",
                                        "tool_create_thought": "记录想法",
                                        "tool_read_thoughts": "查询想法",
                                        "tool_update_thought": "更新想法",
                                        "tool_delete_thought": "删除想法",
                                        "tool_create_schedule": "创建日程",
                                        "tool_read_schedules": "查询日程",
                                        "tool_update_schedule": "更新日程",
                                        "tool_delete_schedule": "删除日程"
                                    }
                                    cn_name = tool_name_mapping.get(func_name, func_name)
                                    status_msg = f"正在执行: {cn_name}..."
                                    
                                    yield f"data: {json.dumps({'type': 'tool_status', 'status': status_msg, 'tool_call_id': tool_calls_accumulator[index].get('id', f'temp_{index}')}, ensure_ascii=False)}\n\n"
                                if tc.function.arguments:
                                    tool_calls_accumulator[index]["function"]["arguments"] += tc.function.arguments

                # 如果本轮没有工具调用，说明大模型认为任务已完成，输出的只是文本
                if not has_tool_calls:
                    # 将本轮的助手回复加入上下文（为了完整性，虽然循环即将结束）
                    if round_content:
                         messages.append({"role": "assistant", "content": round_content})
                    break # 退出 ReAct 循环

                # 如果有工具调用，组装本轮的回复消息加入上下文
                response_message = {
                    "role": "assistant",
                    "content": round_content if round_content else None,
                    "tool_calls": list(tool_calls_accumulator.values())
                }
                messages.append(response_message)
                
                # 检查是否需要用户确认 (增、删、改)
                requires_confirmation = False
                for index, tool_call in tool_calls_accumulator.items():
                    func_name = tool_call["function"]["name"]
                    if func_name not in ["search_web", "tool_read_thoughts", "tool_read_schedules"]:
                        requires_confirmation = True
                        break
                
                if requires_confirmation:
                    action_id = str(uuid.uuid4())
                    # 将需要确认的工具列表发给前端
                    yield f"data: {json.dumps({'type': 'tool_confirmation_required', 'action_id': action_id, 'tool_calls': list(tool_calls_accumulator.values())}, ensure_ascii=False)}\n\n"
                    # 结束当前流，等待前端调用确认接口
                    break
                
                # 如果是前端确认后回传的请求，在第一次循环中我们实际上已经把结果注入到 system prompt 中了
                # 这里为了防止模型死循环调用不需要确认的工具，我们仍然保留执行逻辑
                # 但如果是从前端传回来的已经确认并执行过的工具，不应该再次执行。
                # 注意：这里我们是在循环中，当前 `tool_calls_accumulator` 是大模型新预测的工具调用，并非前端传回的。
                
                # 执行工具并将结果加回对话上下文
                for index, tool_call in tool_calls_accumulator.items():
                    function_name = tool_call["function"]["name"]
                    try:
                        function_args = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        function_args = {}
                        
                    logger.info(f"[User ID: {current_user.id}] Executing tool: {function_name} with args: {function_args}")
                    
                    # 执行工具
                    result = execute_tool(function_name, db, current_user, user_tz=user_tz, **function_args)
                    
                    # 将工具执行结果添加到消息列表
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": function_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    
                    # 可以选择向前端发送工具执行完成的状态
                    yield f"data: {json.dumps({'type': 'tool_status_done', 'status': f'{function_name} 执行完成', 'tool_call_id': tool_call['id']}, ensure_ascii=False)}\n\n"

            # 循环结束，发送结束标记给前端
            yield "data: [DONE]\n\n"
                    
        except Exception as e:
            logger.error(f"[User ID: {current_user.id}] Error in generate: {str(e)}")
            yield f"data: {json.dumps({'type': 'text', 'text': '抱歉，处理您的请求时出现了内部错误，请稍后再试。'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
