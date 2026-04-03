from .schema import THOUGHT_TOOLS_SCHEMA
from .tools import (
    tool_thought_crud_create,
    tool_thought_crud_read,
    tool_thought_crud_update,
    tool_thought_crud_delete
)

# Export the tools registry specific to this skill
THOUGHT_REGISTRY = {
    "thought:crud:create": tool_thought_crud_create,
    "thought:crud:read": tool_thought_crud_read,
    "thought:crud:update": tool_thought_crud_update,
    "thought:crud:delete": tool_thought_crud_delete,
}

__all__ = ["THOUGHT_TOOLS_SCHEMA", "THOUGHT_REGISTRY"]
