from pydantic import BaseModel
from typing import Optional


class RestaurantContext(BaseModel):
    guest_name: str = "Guest"
    dietary_preference: Optional[str] = None


class HandoffData(BaseModel):
    to_agent_name: str
    request_type: str
    short_reason: str
    short_summary: str
