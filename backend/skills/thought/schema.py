THOUGHT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "thought:crud:create",
            "description": "记录用户的想法、笔记或生成长文博客/报告。当用户要求总结、生成博客或报告时，请设定 thought_type 字段。",
            "label": "记录想法/长文",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_content": {"type": "string", "description": "用户原始的想法内容，或生成的长文博客/报告的 Markdown 内容。"},
                    "refined_content": {"type": "string", "description": "AI润色或整理后的想法内容。如果是生成的长文，这里可留空。"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "相关的标签列表，例如：['工作', '日常', '灵感', '周报']"},
                    "thought_type": {"type": "string", "description": "内容类型，可选值包括：'idea' (普通想法, 默认), 'blog' (博客长文), 'weekly_report' (周报), 'fitness_report' (健身报告) 等。"},
                    "source_ids": {"type": "array", "items": {"type": "string"}, "description": "如果有来源想法（例如从多条想法合成博客），在此提供它们的 ID 列表作为字符串数组，例如：['1', '2', '3']。"}
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
