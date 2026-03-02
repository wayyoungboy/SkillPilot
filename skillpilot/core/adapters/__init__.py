"""Platform Adapters for executing skills on different platforms"""

from .base import PlatformAdapter
from .coze import CozeAdapter
from .dify import DifyAdapter
from .langchain import LangChainAdapter

__all__ = [
    "PlatformAdapter",
    "CozeAdapter",
    "DifyAdapter",
    "LangChainAdapter",
    "get_adapter",
]


def get_adapter(platform: str) -> PlatformAdapter:
    """
    Get the appropriate platform adapter.
    
    Args:
        platform: Platform name ('coze', 'dify', 'langchain', 'custom')
        
    Returns:
        Platform adapter instance
    """
    adapters = {
        "coze": CozeAdapter,
        "dify": DifyAdapter,
        "langchain": LangChainAdapter,
        "custom": PlatformAdapter,
    }
    
    adapter_class = adapters.get(platform.lower(), PlatformAdapter)
    return adapter_class()
