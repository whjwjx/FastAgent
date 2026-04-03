from .schema import SEARCH_TOOLS_SCHEMA
from .tools import tool_search_web

SEARCH_REGISTRY = {
    "search_web": tool_search_web,
}

__all__ = ["SEARCH_TOOLS_SCHEMA", "SEARCH_REGISTRY"]
