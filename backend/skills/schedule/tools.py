from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
from models.models import Schedule, User

logger = logging.getLogger(__name__)

def tool_schedule_crud_create(db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    start_time_str = kwargs.get("start_time")
    logger.info(f"[ScheduleSkill] Creating schedule for user {current_user.id}, title: {kwargs.get('title')}, start: {start_time_str}")
    if start_time_str and len(start_time_str) == 10:
        start_time_str += "T07:00:00"
    
    try:
        start_time = datetime.fromisoformat(start_time_str)
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=user_tz)
        start_time = start_time.astimezone(timezone.utc)
    except ValueError:
        logger.error(f"[ScheduleSkill] Time format error: {start_time_str}")
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
            logger.error(f"[ScheduleSkill] End time format error: {end_time_str}")
            return {"status": "error", "message": f"结束时间格式错误: {end_time_str}"}

    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    logger.info(f"[ScheduleSkill] Created schedule ID: {schedule.id}")
    return {"status": "success", "message": "日程创建成功", "schedule_id": schedule.id}

def tool_schedule_crud_read(db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    logger.info(f"[ScheduleSkill] Reading schedules for user {current_user.id}")
    query = db.query(Schedule).filter(Schedule.user_id == current_user.id, Schedule.is_deleted == False)
    schedules = query.order_by(Schedule.start_time.asc()).limit(10).all()
    if not schedules:
        logger.info(f"[ScheduleSkill] No schedules found")
        return {"status": "success", "message": "未找到相关日程", "data": []}
        
    logger.info(f"[ScheduleSkill] Found {len(schedules)} schedules")
    return {"status": "success", "data": [{"id": s.id, "title": s.title, "start_time": str(s.start_time.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'))} for s in schedules]}

def tool_schedule_crud_update(db: Session, current_user: User, user_tz=timezone.utc, **kwargs):
    schedule_id = kwargs.get("schedule_id")
    logger.info(f"[ScheduleSkill] Updating schedule {schedule_id} for user {current_user.id}")
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == current_user.id, Schedule.is_deleted == False).first()
    if not schedule:
        logger.warning(f"[ScheduleSkill] Schedule {schedule_id} not found")
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
            logger.warning(f"[ScheduleSkill] Updated start time format error: {start_time_str}")
            pass
            
    db.commit()
    logger.info(f"[ScheduleSkill] Updated schedule {schedule_id} successfully")
    return {"status": "success", "message": f"日程(ID:{schedule_id})已更新"}

def tool_schedule_crud_delete(db: Session, current_user: User, **kwargs):
    schedule_ids = kwargs.get("schedule_ids", [])
    if "schedule_id" in kwargs:
        schedule_ids.append(kwargs.get("schedule_id"))
    
    logger.info(f"[ScheduleSkill] Deleting schedules {schedule_ids} for user {current_user.id}")
    if not schedule_ids:
        logger.warning(f"[ScheduleSkill] No IDs provided for deletion")
        return {"status": "error", "message": "未提供要删除的日程ID"}
        
    schedules = db.query(Schedule).filter(
        Schedule.id.in_(schedule_ids), 
        Schedule.user_id == current_user.id, 
        Schedule.is_deleted == False
    ).all()
    
    if not schedules:
        logger.warning(f"[ScheduleSkill] No schedules found for deletion")
        return {"status": "error", "message": f"未找到指定的日程"}
        
    deleted_count = 0
    for schedule in schedules:
        schedule.is_deleted = True
        deleted_count += 1
        
    db.commit()
    logger.info(f"[ScheduleSkill] Successfully deleted {deleted_count} schedules")
    return {"status": "success", "message": f"成功删除了 {deleted_count} 个日程"}
