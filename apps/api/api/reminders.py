from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.deps import get_current_user
from database.db import get_db
from database.models import Appliance, Reminder, User
from schemas.reminders import ReminderCreateRequest, ReminderResponse

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


def _build_dedupe_key(user_id: int, appliance_id: int, reminder_type: str, due_at) -> str:
    utc_due = due_at.astimezone(timezone.utc)
    return f"{user_id}:{appliance_id}:{reminder_type}:{utc_due.date().isoformat()}"


@router.post("", response_model=ReminderResponse)
def create_reminder(
    payload: ReminderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appliance = (
        db.query(Appliance)
        .filter(Appliance.id == payload.appliance_id)
        .filter(Appliance.user_id == current_user.id)
        .first()
    )
    if not appliance:
        raise HTTPException(status_code=404, detail="Appliance not found")

    dedupe_key = _build_dedupe_key(current_user.id, payload.appliance_id, payload.reminder_type, payload.due_at)
    exists = db.query(Reminder).filter(Reminder.dedupe_key == dedupe_key).first()
    if exists:
        return ReminderResponse(
            id=exists.id,
            appliance_id=exists.appliance_id,
            reminder_type=exists.reminder_type,
            due_at=exists.due_at,
            status=exists.status,
        )

    row = Reminder(
        user_id=current_user.id,
        appliance_id=payload.appliance_id,
        reminder_type=payload.reminder_type,
        due_at=payload.due_at.astimezone(timezone.utc).replace(tzinfo=None),
        dedupe_key=dedupe_key,
        status="scheduled",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return ReminderResponse(
        id=row.id,
        appliance_id=row.appliance_id,
        reminder_type=row.reminder_type,
        due_at=row.due_at,
        status=row.status,
    )


@router.get("", response_model=list[ReminderResponse])
def list_reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Reminder).filter(Reminder.user_id == current_user.id).order_by(Reminder.due_at.asc()).all()
    return [
        ReminderResponse(
            id=row.id,
            appliance_id=row.appliance_id,
            reminder_type=row.reminder_type,
            due_at=row.due_at,
            status=row.status,
        )
        for row in rows
    ]
