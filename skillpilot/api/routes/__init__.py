"""API Routes Module"""

from . import auth, orchestration, platform, skill, vector_search

__all__ = [
    "auth",
    "skill",
    "orchestration",
    "vector_search",
    "platform",
]
