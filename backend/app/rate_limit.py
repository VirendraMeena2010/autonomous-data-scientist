"""from __future__ import annotations

# 1. Change SlowAPI to Limiter
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# 2. Swap the instantiation class name to Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.rate_limit_default_per_minute} per minute",
    ],
    storage_uri=settings.redis_url,
    strategy="moving-window",
)
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.rate_limit_default_per_minute} per minute",
    ],
    storage_uri="memory://",
    strategy="moving-window",
)