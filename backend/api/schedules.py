from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from database.session import get_db
from models.models import Schedule, User
from schemas.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from api.deps import get_current_user
from sqlalchemy import extract, func

router = APIRouter()

@router.post("/", response_model=ScheduleResponse)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_schedule = Schedule(**schedule.model_dump(), user_id=current_user.id)
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/", response_model=List[ScheduleResponse])
def get_schedules(
    view_type: Optional[str] = Query("all", description="View type: day, week, month, or all"),
    target_date: Optional[date] = Query(None, description="Target date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Schedule).filter(Schedule.user_id == current_user.id, Schedule.is_deleted == False)
    
    if view_type != "all" and target_date:
        if view_type == "day":
            query = query.filter(func.date(Schedule.start_time) == target_date)
        elif view_type == "month":
            query = query.filter(
                extract('year', Schedule.start_time) == target_date.year,
                extract('month', Schedule.start_time) == target_date.month
            )
        # Week view can be implemented with start/end of week logic based on target_date if needed.
        
    return query.order_by(Schedule.start_time.asc()).all()

@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int, 
    schedule_update: ScheduleUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == current_user.id, Schedule.is_deleted == False).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    update_data = schedule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_schedule, key, value)
        
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == current_user.id, Schedule.is_deleted == False).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    db_schedule.is_deleted = True
    db.commit()
    return {"message": "Schedule deleted successfully"}
