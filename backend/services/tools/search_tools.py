import os
from sqlalchemy.orm import Session
from models.models import User
from tavily import TavilyClient
from core.config import settings

def tool_search_web(db: Session, current_user: User, **kwargs):
    query = kwargs.get("query")
    if not query:
        return {"status": "error", "message": "未提供搜索关键词"}
    
    api_key = settings.TAVILY_API_KEY or os.environ.get("TAVILY_API_KEY")
    if not api_key:
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
        return {"status": "success", "data": results, "message": f"成功检索到关于 '{query}' 的信息"}
    except Exception as e:
        return {"status": "error", "message": f"搜索执行失败: {str(e)}"}

SEARCH_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "联网搜索工具。当你需要获取最新资讯、实时信息或你的静态知识库无法回答的问题时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词，尽量精准"}
                },
                "required": ["query"]
            }
        }
    }
]