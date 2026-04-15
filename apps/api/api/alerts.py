from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import AlertNotification
from schemas.alerts import AlertResponse, AlertsBootstrapRequest, AlertStatusUpdateRequest

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _owner_key_from_header(x_homeops_user_key: str | None = Header(default=None, alias="X-HomeOps-User-Key")) -> str:
    candidate = (x_homeops_user_key or "").strip()
    if len(candidate) < 8 or len(candidate) > 120:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing or invalid X-HomeOps-User-Key")
    return candidate


def _to_response(row: AlertNotification) -> AlertResponse:
    return AlertResponse(
        id=row.id,
        title=row.title,
        time=row.time_label,
        severity=row.severity,
        desc=row.description,
        status=row.status,
    )


@router.post("/bootstrap", response_model=list[AlertResponse])
def bootstrap_alerts(
    payload: AlertsBootstrapRequest,
    db: Session = Depends(get_db),
    owner_key: str = Depends(_owner_key_from_header),
):
    existing = (
        db.query(AlertNotification)
        .filter(AlertNotification.owner_key == owner_key)
        .order_by(AlertNotification.id.asc())
        .all()
    )
    if existing:
        return [_to_response(row) for row in existing]

    rows: list[AlertNotification] = []
    now = datetime.utcnow()
    for item in payload.alerts:
        row = AlertNotification(
            owner_key=owner_key,
            dedupe_key=item.title.strip().lower(),
            title=item.title,
            time_label=item.time,
            severity=item.severity,
            description=item.desc,
            status="active",
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)

    return [_to_response(row) for row in rows]


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    db: Session = Depends(get_db),
    owner_key: str = Depends(_owner_key_from_header),
):
    rows = (
        db.query(AlertNotification)
        .filter(AlertNotification.owner_key == owner_key)
        .order_by(AlertNotification.id.asc())
        .all()
    )
    return [_to_response(row) for row in rows]


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert_status(
    alert_id: int,
    payload: AlertStatusUpdateRequest,
    db: Session = Depends(get_db),
    owner_key: str = Depends(_owner_key_from_header),
):
    row = (
        db.query(AlertNotification)
        .filter(AlertNotification.id == alert_id)
        .filter(AlertNotification.owner_key == owner_key)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    row.status = payload.status
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)

    return _to_response(row)
