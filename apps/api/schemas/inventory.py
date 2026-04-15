from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

InventoryStatus = Literal["good", "attention", "critical"]
ServiceEventType = Literal["serviced", "repaired", "inspected", "note", "replaced", "other"]


class ServiceHistoryCreate(BaseModel):
    event_type: ServiceEventType = "serviced"
    event_date: date
    description: Optional[str] = Field(None, max_length=2000)
    technician: Optional[str] = Field(None, max_length=120)
    cost: Optional[str] = Field(None, max_length=40)


class ServiceHistoryResponse(BaseModel):
    id: int
    item_id: int
    event_type: str
    event_date: date
    description: Optional[str]
    technician: Optional[str]
    cost: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class InventoryItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=180)
    category: str = Field("Appliances", max_length=80)
    brand: Optional[str] = Field(None, max_length=120)
    model_number: str = Field(..., min_length=1, max_length=120)
    serial_number: Optional[str] = Field(None, max_length=120)
    purchase_date: date | None = None
    last_serviced: date | None = None
    next_maintenance: Optional[str] = Field("30 days", max_length=80)
    notes: Optional[str] = Field(None, max_length=4000)
    status: InventoryStatus = "good"
    health: int = Field(85, ge=0, le=100)


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=180)
    category: Optional[str] = Field(None, max_length=80)
    brand: Optional[str] = Field(None, max_length=120)
    model_number: Optional[str] = Field(None, min_length=1, max_length=120)
    serial_number: Optional[str] = Field(None, max_length=120)
    purchase_date: date | None = None
    last_serviced: date | None = None
    next_maintenance: Optional[str] = Field(None, max_length=80)
    notes: Optional[str] = Field(None, max_length=4000)
    status: Optional[InventoryStatus] = None
    health: Optional[int] = Field(None, ge=0, le=100)


class InventoryItemResponse(BaseModel):
    id: int
    name: str
    category: str
    brand: Optional[str]
    model_number: str
    serial_number: Optional[str]
    purchase_date: date | None
    last_serviced: date | None
    next_maintenance: Optional[str]
    notes: Optional[str]
    status: str
    health: int
    created_at: datetime
    updated_at: datetime
    history: list[ServiceHistoryResponse] = []

    model_config = {"from_attributes": True}
