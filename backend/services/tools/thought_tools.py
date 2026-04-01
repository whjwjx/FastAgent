from sqlalchemy.orm import Session
from models.models import Thought, User
from services.embedding_service import get_embedding
import logging

logger = logging.getLogger(__name__)

def tool_thought_crud_create(db: Session, current_user: User, **kwargs):
    original_content = kwargs.get("original_content")
    refined_content = kwargs.get("refined_content")
    
    # Generate embedding based on original content
    logger.info(f"[ThoughtSkill] Creating thought for user {current_user.id}")
    embedding = get_embedding(original_content) if original_content else None
    
    thought = Thought(
        user_id=current_user.id,
        original_content=original_content,
        refined_content=refined_content,
        tags=kwargs.get("tags"),
        embedding=embedding
    )
    db.add(thought)
    db.commit()
    db.refresh(thought)
    logger.info(f"[ThoughtSkill] Created thought ID: {thought.id}")
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

THOUGHT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "thought:crud:create",
            "description": "记录用户的想法、笔记或灵感",
            "label": "记录想法",
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
            "name": "thought:crud:read",
            "description": "查询/读取用户记录过的想法",
            "label": "查询想法",
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
            "name": "thought:crud:update",
            "description": "更新已有的想法内容",
            "label": "更新想法",
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
            "name": "thought:crud:delete",
            "description": "删除已有的想法，支持批量删除",
            "label": "删除想法",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "需要删除的想法ID列表，例如：[1, 2, 3]"
                    }
                },
                "required": ["thought_ids"]
            }
        }
    }
]