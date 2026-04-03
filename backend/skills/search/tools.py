import os
import logging
from sqlalchemy.orm import Session
from models.models import User
from tavily import TavilyClient
from core.config import settings

logger = logging.getLogger(__name__)

def tool_search_web(db: Session, current_user: User, **kwargs):
    query = kwargs.get("query")
    logger.info(f"[SearchSkill] Searching web for user {current_user.id}, query: {query}")
    if not query:
        logger.warning(f"[SearchSkill] No query provided")
        return {"status": "error", "message": "未提供搜索关键词"}
    
    api_key = settings.TAVILY_API_KEY or os.environ.get("TAVILY_API_KEY")
    if not api_key:
        logger.error(f"[SearchSkill] Tavily API Key not configured")
        return {"status": "error", "message": "Tavily API Key 未配置，无法执行搜索"}
        
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="advanced"
        )
        # 提取相关信息返回给大模型
        results = []
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", "")
            })
        logger.info(f"[SearchSkill] Found {len(results)} results for '{query}'")
        return {"status": "success", "data": results, "message": f"成功检索到关于 '{query}' 的信息"}
    except Exception as e:
        logger.error(f"[SearchSkill] Search failed: {str(e)}")
        return {"status": "error", "message": f"搜索执行失败: {str(e)}"}
