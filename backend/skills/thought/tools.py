from sqlalchemy.orm import Session
from models.models import Thought, User
from services.embedding_service import get_embedding
import logging

logger = logging.getLogger(__name__)

def tool_thought_crud_create(db: Session, current_user: User, **kwargs):
    original_content = kwargs.get("original_content")
    refined_content = kwargs.get("refined_content")
    thought_type = kwargs.get("thought_type", "idea")
    source_ids = kwargs.get("source_ids")
    
    # Generate embedding based on original content
    logger.info(f"[ThoughtSkill] Creating thought for user {current_user.id}, type: {thought_type}")
    embedding = get_embedding(original_content) if original_content else None
    
    thought = Thought(
        user_id=current_user.id,
        original_content=original_content,
        refined_content=refined_content,
        tags=kwargs.get("tags"),
        thought_type=thought_type,
        source_ids=source_ids,
        embedding=embedding
    )
    db.add(thought)
    db.commit()
    db.refresh(thought)
    logger.info(f"[ThoughtSkill] Created thought ID: {thought.id}, type: {thought_type}")
    return {"status": "success", "message": "想法记录成功", "thought_id": thought.id}

def tool_thought_crud_read(db: Session, current_user: User, **kwargs):
    keyword = kwargs.get("keyword")
    logger.info(f"[ThoughtSkill] Reading thoughts for user {current_user.id}, keyword: {keyword}")
    query = db.query(Thought).filter(Thought.user_id == current_user.id, Thought.is_deleted == False)
    if keyword:
        query = query.filter(
            (Thought.original_content.ilike(f"%{keyword}%")) | 
            (Thought.refined_content.ilike(f"%{keyword}%"))
        )
    thoughts = query.order_by(Thought.created_at.desc()).limit(10).all()
    if not thoughts:
        logger.info(f"[ThoughtSkill] No thoughts found")
        return {"status": "success", "message": "未找到相关的想法", "data": []}
    
    logger.info(f"[ThoughtSkill] Found {len(thoughts)} thoughts")
    return {"status": "success", "data": [{"id": t.id, "content": t.original_content, "created_at": str(t.created_at)} for t in thoughts]}

def tool_thought_crud_update(db: Session, current_user: User, **kwargs):
    thought_id = kwargs.get("thought_id")
    logger.info(f"[ThoughtSkill] Updating thought {thought_id} for user {current_user.id}")
    thought = db.query(Thought).filter(Thought.id == thought_id, Thought.user_id == current_user.id, Thought.is_deleted == False).first()
    if not thought:
        logger.warning(f"[ThoughtSkill] Thought {thought_id} not found")
        return {"status": "error", "message": f"未找到ID为{thought_id}的想法"}
    
    if "original_content" in kwargs:
        thought.original_content = kwargs["original_content"]
        # Regenerate embedding if content is updated
        thought.embedding = get_embedding(kwargs["original_content"])
    if "refined_content" in kwargs:
        thought.refined_content = kwargs["refined_content"]
    if "tags" in kwargs:
        thought.tags = kwargs["tags"]
        
    db.commit()
    logger.info(f"[ThoughtSkill] Updated thought {thought_id} successfully")
    return {"status": "success", "message": f"想法(ID:{thought_id})已更新"}

def tool_thought_crud_delete(db: Session, current_user: User, **kwargs):
    thought_ids = kwargs.get("thought_ids", [])
    if "thought_id" in kwargs:
        thought_ids.append(kwargs.get("thought_id"))
    
    logger.info(f"[ThoughtSkill] Deleting thoughts {thought_ids} for user {current_user.id}")
    if not thought_ids:
        logger.warning(f"[ThoughtSkill] No IDs provided for deletion")
        return {"status": "error", "message": "未提供要删除的想法ID"}
        
    thoughts = db.query(Thought).filter(
        Thought.id.in_(thought_ids), 
        Thought.user_id == current_user.id, 
        Thought.is_deleted == False
    ).all()
    
    if not thoughts:
        logger.warning(f"[ThoughtSkill] No thoughts found for deletion")
        return {"status": "error", "message": f"未找到指定的想法"}
        
    deleted_count = 0
    for thought in thoughts:
        thought.is_deleted = True
        deleted_count += 1
        
    db.commit()
    logger.info(f"[ThoughtSkill] Successfully deleted {deleted_count} thoughts")
    return {"status": "success", "message": f"成功删除了 {deleted_count} 条想法"}
