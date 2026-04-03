SCHEDULE_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "schedule:crud:create",
            "description": "创建一个日程、提醒或待办事项",
            "label": "创建日程",
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
            "name": "schedule:crud:read",
            "description": "查询/读取用户的日程安排",
            "label": "查询日程",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule:crud:update",
            "description": "更新已有的日程",
            "label": "更新日程",
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
            "name": "schedule:crud:delete",
            "description": "删除（取消）已有的日程，支持批量删除",
            "label": "删除日程",
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
