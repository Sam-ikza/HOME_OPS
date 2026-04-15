from pydantic import BaseModel, Field


class ProHandoffRequest(BaseModel):
    appliance_id: int
    issue_summary: str = Field(min_length=3)
    city: str | None = None


class PartsLinkRequest(BaseModel):
    appliance_id: int
    part_query: str = Field(min_length=2)


class ToolResponse(BaseModel):
    tool_name: str
    payload: dict
