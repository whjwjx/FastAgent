from sqlalchemy.orm import Session
from datetime import datetime, timezone
from models.models import Schedule, User

def tool_create_schedule(db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    start_time_str = kwargs.get("start_time")
    if start_time_str and len(start_time_str) == 10:
        start_time_str += "T07:00:00"
    
    try:
        start_time = datetime.fromisoformat(start_time_str)
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=user_tz)
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
        if len(end_time_str) == 10:
            end_time_str += "T07:00:00"
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
    query = db.query(Schedule).filter(Schedule.user_id == current_user.id, Schedule.is_deleted == False)
    schedules = query.order_by(Schedule.start_time.asc()).limit(10).all()
    if not schedules:
        return {"status": "success", "message": "未找到相关日程", "data": []}
        
    return {"status": "success", "data": [{"id": s.id, "title": s.title, "start_time": str(s.start_time.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'))} for s in schedules]}

def tool_update_schedule(db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    schedule_id = kwargs.get("schedule_id")
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == current_user.id, Schedule.is_deleted == False).first()
    if not schedule:
        return {"status": "error", "message": f"未找到ID为{schedule_id}的日程"}
    
    if "title" in kwargs:
        schedule.title = kwargs["title"]
    if "start_time" in kwargs:
        start_time_str = kwargs["start_time"]
        if start_time_str and len(start_time_str) == 10:
            start_time_str += "T07:00:00"
        try:
            start_time = datetime.fromisoformat(start_time_str)
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=user_tz)
            schedule.start_time = start_time.astimezone(timezone.utc)
        except ValueError:
            pass
            
    db.commit()
    return {"status": "success", "message": f"日程(ID:{schedule_id})已更新"}

def tool_delete_schedule(db: Session, current_user: User, **kwargs):
    schedule_ids = kwargs.get("schedule_ids", [])
    if "schedule_id" in kwargs:
        schedule_ids.append(kwargs.get("schedule_id"))
        
    if not schedule_ids:
        return {"status": "error", "message": "未提供要删除的日程ID"}
        
    schedules = db.query(Schedule).filter(
        Schedule.id.in_(schedule_ids), 
        Schedule.user_id == current_user.id, 
        Schedule.is_deleted == False
    ).all()
    
    if not schedules:
        return {"status": "error", "message": f"未找到指定的日程"}
        
    deleted_count = 0
    for schedule in schedules:
        schedule.is_deleted = True
        deleted_count += 1
        
    db.commit()
    return {"status": "success", "message": f"成功删除了 {deleted_count} 个日程"}

SCHEDULE_TOOLS_SCHEMA = [
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
            "description": "删除（取消）已有的日程，支持批量删除",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要删除的日程ID列表，例如：[1, 2, 3]"
                    }
                },
                "required": ["schedule_ids"]
            }
        }
    }
]