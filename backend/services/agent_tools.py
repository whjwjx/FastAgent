import json
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from models.models import Thought, Schedule, User

def tool_create_thought(db: Session, current_user: User, **kwargs):
    thought = Thought(
        user_id=current_user.id,
        original_content=kwargs.get("original_content"),
        refined_content=kwargs.get("refined_content"),
        tags=kwargs.get("tags")
    )
    db.add(thought)
    db.commit()
    db.refresh(thought)
    return {"status": "success", "message": "想法记录成功", "thought_id": thought.id}

def tool_read_thoughts(db: Session, current_user: User, **kwargs):
    keyword = kwargs.get("keyword")
    query = db.query(Thought).filter(Thought.user_id == current_user.id, Thought.is_deleted == False)
    if keyword:
        query = query.filter(
            (Thought.original_content.ilike(f"%{keyword}%")) | 
            (Thought.refined_content.ilike(f"%{keyword}%"))
        )
    thoughts = query.order_by(Thought.created_at.desc()).limit(10).all()
    if not thoughts:
        return {"status": "success", "message": "未找到相关的想法", "data": []}
    return {"status": "success", "data": [{"id": t.id, "content": t.original_content, "created_at": str(t.created_at)} for t in thoughts]}

def tool_update_thought(db: Session, current_user: User, **kwargs):
    thought_id = kwargs.get("thought_id")
    thought = db.query(Thought).filter(Thought.id == thought_id, Thought.user_id == current_user.id, Thought.is_deleted == False).first()
    if not thought:
        return {"status": "error", "message": f"未找到ID为{thought_id}的想法"}
    
    if "original_content" in kwargs:
        thought.original_content = kwargs["original_content"]
    if "refined_content" in kwargs:
        thought.refined_content = kwargs["refined_content"]
    if "tags" in kwargs:
        thought.tags = kwargs["tags"]
        
    db.commit()
    return {"status": "success", "message": f"想法(ID:{thought_id})已更新"}

def tool_delete_thought(db: Session, current_user: User, **kwargs):
    thought_id = kwargs.get("thought_id")
    thought = db.query(Thought).filter(Thought.id == thought_id, Thought.user_id == current_user.id, Thought.is_deleted == False).first()
    if not thought:
        return {"status": "error", "message": f"未找到ID为{thought_id}的想法"}
    
    thought.is_deleted = True
    db.commit()
    return {"status": "success", "message": f"想法(ID:{thought_id})已删除"}

def tool_create_schedule(db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    start_time_str = kwargs.get("start_time")
    try:
        start_time = datetime.fromisoformat(start_time_str)
        if start_time.tzinfo is None:
            # Model outputs naive local time (e.g. 14:00). We attach user's local timezone.
            start_time = start_time.replace(tzinfo=user_tz)
        # Convert to UTC before storing in database
        start_time = start_time.astimezone(timezone.utc)
    except ValueError:
        return {"status": "error", "message": f"时间格式错误: {start_time_str}"}

    schedule = Schedule(
        user_id=current_user.id,
        title=kwargs.get("title"),
        start_time=start_time,
        location=kwargs.get("location")
    )
    
    end_time_str = kwargs.get("end_time")
    if end_time_str:
        try:
            end_time = datetime.fromisoformat(end_time_str)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=user_tz)
            schedule.end_time = end_time.astimezone(timezone.utc)
        except ValueError:
            return {"status": "error", "message": f"结束时间格式错误: {end_time_str}"}

    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return {"status": "success", "message": "日程创建成功", "schedule_id": schedule.id}

def tool_read_schedules(db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    # Could filter by time range
    query = db.query(Schedule).filter(Schedule.user_id == current_user.id, Schedule.is_deleted == False)
    schedules = query.order_by(Schedule.start_time.asc()).limit(10).all()
    if not schedules:
        return {"status": "success", "message": "未找到相关日程", "data": []}
        
    # Return time in user's local timezone so LLM can understand and speak naturally
    return {"status": "success", "data": [{"id": s.id, "title": s.title, "start_time": str(s.start_time.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'))} for s in schedules]}

def tool_update_schedule(db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    schedule_id = kwargs.get("schedule_id")
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == current_user.id, Schedule.is_deleted == False).first()
    if not schedule:
        return {"status": "error", "message": f"未找到ID为{schedule_id}的日程"}
    
    if "title" in kwargs:
        schedule.title = kwargs["title"]
    if "start_time" in kwargs:
        try:
            start_time = datetime.fromisoformat(kwargs["start_time"])
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=user_tz)
            schedule.start_time = start_time.astimezone(timezone.utc)
        except ValueError:
            pass
            
    db.commit()
    return {"status": "success", "message": f"日程(ID:{schedule_id})已更新"}

def tool_delete_schedule(db: Session, current_user: User, **kwargs):
    schedule_id = kwargs.get("schedule_id")
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == current_user.id, Schedule.is_deleted == False).first()
    if not schedule:
        return {"status": "error", "message": f"未找到ID为{schedule_id}的日程"}
    
    schedule.is_deleted = True
    db.commit()
    return {"status": "success", "message": f"日程(ID:{schedule_id})已删除"}

# Tool Registry
TOOL_REGISTRY = {
    "create_thought": tool_create_thought,
    "read_thoughts": tool_read_thoughts,
    "update_thought": tool_update_thought,
    "delete_thought": tool_delete_thought,
    "create_schedule": tool_create_schedule,
    "read_schedules": tool_read_schedules,
    "update_schedule": tool_update_schedule,
    "delete_schedule": tool_delete_schedule
}

def execute_tool(tool_name: str, db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    if tool_name not in TOOL_REGISTRY:
        return {"status": "error", "message": f"未知工具: {tool_name}"}
    try:
        # 针对需要 timezone 的函数，自动注入 user_tz
        if tool_name in ["create_schedule", "read_schedules", "update_schedule"]:
            return TOOL_REGISTRY[tool_name](db, current_user, user_tz=user_tz, **kwargs)
        else:
            return TOOL_REGISTRY[tool_name](db, current_user, **kwargs)
    except Exception as e:
        return {"status": "error", "message": f"工具执行异常: {str(e)}"}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_thought",
            "description": "记录用户的想法、笔记或灵感",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_content": {"type": "string", "description": "用户原始的想法内容"},
                    "refined_content": {"type": "string", "description": "AI润色或整理后的想法内容"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "相关的标签列表，例如：['工作', '日常', '灵感']"}
                },
                "required": ["original_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_thoughts",
            "description": "查询/读取用户记录过的想法",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词，如果不提供则返回最近的想法"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_thought",
            "description": "更新已有的想法内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought_id": {"type": "integer", "description": "要更新的想法ID"},
                    "original_content": {"type": "string", "description": "更新后的内容"},
                    "refined_content": {"type": "string", "description": "更新后的润色内容"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "更新后的标签列表"}
                },
                "required": ["thought_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_thought",
            "description": "删除（归档）一条想法",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought_id": {"type": "integer", "description": "要删除的想法ID"}
                },
                "required": ["thought_id"]
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
                    "title": {"type": "string", "description": "日程标题"},
                    "start_time": {"type": "string", "description": "开始时间，ISO格式 (YYYY-MM-DDTHH:MM:SS) 或者 YYYY-MM-DD"},
                    "end_time": {"type": "string", "description": "结束时间，ISO格式 (YYYY-MM-DDTHH:MM:SS) 或者 YYYY-MM-DD"},
                    "location": {"type": "string", "description": "地点，如果没有则为空"}
                },
                "required": ["title", "start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_schedules",
            "description": "查询/读取用户的日程安排",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_schedule",
            "description": "更新已有的日程",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "integer", "description": "要更新的日程ID"},
                    "title": {"type": "string", "description": "更新后的标题"},
                    "start_time": {"type": "string", "description": "更新后的开始时间，ISO格式"}
                },
                "required": ["schedule_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_schedule",
            "description": "删除（取消）一条日程",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "integer", "description": "要删除的日程ID"}
                },
                "required": ["schedule_id"]
            }
        }
    }
]
