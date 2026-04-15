from typing import Literal

from pydantic import BaseModel, Field

AlertSeverity = Literal["high", "medium", "low"]
AlertStatus = Literal["active", "dismissed", "actioned"]


class AlertSeedItem(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    time: str = Field(min_length=1, max_length=60)
    severity: AlertSeverity
    desc: str = Field(min_length=3, max_length=500)


class AlertsBootstrapRequest(BaseModel):
    alerts: list[AlertSeedItem] = Field(default_factory=list, max_length=25)


class AlertStatusUpdateRequest(BaseModel):
    status: AlertStatus


class AlertResponse(BaseModel):
    id: int
    title: str
    time: str
    severity: AlertSeverity
    desc: str
    status: AlertStatus
