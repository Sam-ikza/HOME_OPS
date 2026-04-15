from datetime import datetime

from pydantic import BaseModel, Field


class ReminderCreateRequest(BaseModel):
    appliance_id: int
    reminder_type: str = Field(min_length=2, max_length=80)
    due_at: datetime


class ReminderResponse(BaseModel):
    id: int
    appliance_id: int
    reminder_type: str
    due_at: datetime
    status: str
