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
