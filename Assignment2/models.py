from pydantic import BaseModel


class RestaurantContext(BaseModel):
    guest_name: str = "Guest"


class HandoffData(BaseModel):
    to_agent_name: str
    request_type: str
    short_reason: str
    short_summary: str


class InputGuardrailOutput(BaseModel):
    is_blocked: bool
    reason: str


class OutputGuardrailOutput(BaseModel):
    is_blocked: bool
    reason: str
