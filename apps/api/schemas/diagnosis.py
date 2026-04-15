from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PhysicalBrief(BaseModel):
    estimated_time_minutes: int = Field(ge=0)
    heavy_lifting_required: bool
    estimated_weight_lbs: float = Field(ge=0)
    spill_risk: Literal["LOW", "MEDIUM", "HIGH"]


class Citation(BaseModel):
    manual_id: int | None = None
    chunk_id: int | None = None
    source: str = "manual"
    snippet: str


class DiagnosisRequest(BaseModel):
    appliance_id: int
    issue_text: str = Field(min_length=3)


class DiagnosisResponse(BaseModel):
    danger_level: Literal["LOW", "MEDIUM", "HIGH"]
    call_pro: bool
    warranty_active: bool
    warranty_block_reason: str | None = None
    manufacturer_support: str | None = None
    fragility_warning: str
    physical_brief: PhysicalBrief
    software_lock_warning: str | None = None
    diagnosis_summary: str
    diy_steps: list[str]
    required_parts: list[str]
    citations: list[Citation]
    escalation_message: str


class DiagnosisRecordResponse(BaseModel):
    id: int
    appliance_id: int
    issue_text: str
    response: DiagnosisResponse
    created_at: datetime


class ImageDiagnosisExtraction(BaseModel):
    appliance_type: str | None = None
    brand: str = "Unknown"
    model_number: str = "Unknown"
    error_code: str | None = None
    display_text: str | None = None
    likely_issue: str = "Unable to determine from image."
    visible_signals: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    summary: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    needs_confirmation: bool = False
    source: str = "gemini"


class ImageDiagnosisResponse(BaseModel):
    extraction: ImageDiagnosisExtraction
    diagnosis: DiagnosisResponse
    chat_prompt: str
    event_id: int | None = None


class ImageDiagnosisHistoryItem(BaseModel):
    id: int
    inventory_item_id: int | None = None
    issue_text: str
    extraction: ImageDiagnosisExtraction
    diagnosis: DiagnosisResponse
    created_at: datetime
