from .schema import SCHEDULE_TOOLS_SCHEMA
from .tools import (
    tool_schedule_crud_create,
    tool_schedule_crud_read,
    tool_schedule_crud_update,
    tool_schedule_crud_delete
)

SCHEDULE_REGISTRY = {
    "schedule:crud:create": tool_schedule_crud_create,
    "schedule:crud:read": tool_schedule_crud_read,
    "schedule:crud:update": tool_schedule_crud_update,
    "schedule:crud:delete": tool_schedule_crud_delete,
}

__all__ = ["SCHEDULE_TOOLS_SCHEMA", "SCHEDULE_REGISTRY"]
