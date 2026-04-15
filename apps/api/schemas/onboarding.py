from datetime import date

from pydantic import BaseModel, Field


class OCRExtraction(BaseModel):
    brand: str = Field(default="Unknown")
    model_number: str = Field(default="Unknown")
    serial_number: str | None = None
    purchase_date: date | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    needs_confirmation: bool = False
    raw_response: str | None = None


class ApplianceResponse(BaseModel):
    id: int
    brand: str
    model_number: str
    serial_number: str | None
    purchase_date: date | None
    warranty_active: bool


class ManualIngestResponse(BaseModel):
    manual_id: int
    chunk_count: int
    source: str


class ManualUrlIngestRequest(BaseModel):
    appliance_id: int
    url: str
    title: str | None = None
