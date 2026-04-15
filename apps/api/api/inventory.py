from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from database.db import SessionLocal
from database.models import ApplianceServiceHistory, InventoryItemRecord
from schemas.inventory import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    ServiceHistoryCreate,
    ServiceHistoryResponse,
)

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

_MIN_KEY_LEN = 8
_MAX_KEY_LEN = 120


def _owner_key_from_header(x_homeops_user_key: str = Header(None)) -> str:
    if not x_homeops_user_key or not (_MIN_KEY_LEN <= len(x_homeops_user_key) <= _MAX_KEY_LEN):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-HomeOps-User-Key header is required (8-120 chars).",
        )
    return x_homeops_user_key


# ---------------------------------------------------------------------------
# CRUD – inventory items
# ---------------------------------------------------------------------------

@router.get("", response_model=list[InventoryItemResponse])
def list_inventory(x_homeops_user_key: str = Header(None)):
    owner_key = _owner_key_from_header(x_homeops_user_key)
    with SessionLocal() as db:
        records = (
            db.query(InventoryItemRecord)
            .filter(InventoryItemRecord.owner_key == owner_key)
            .order_by(InventoryItemRecord.created_at.desc())
            .all()
        )
        return [InventoryItemResponse.model_validate(r) for r in records]


@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_item(payload: InventoryItemCreate, x_homeops_user_key: str = Header(None)):
    owner_key = _owner_key_from_header(x_homeops_user_key)
    try:
        with SessionLocal() as db:
            record = InventoryItemRecord(
                owner_key=owner_key,
                name=payload.name,
                category=payload.category,
                brand=payload.brand,
                model_number=payload.model_number,
                serial_number=payload.serial_number,
                purchase_date=payload.purchase_date,
                last_serviced=payload.last_serviced,
                next_maintenance=payload.next_maintenance,
                notes=payload.notes,
                status=payload.status,
                health=payload.health,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            # seed an initial "added" history entry
            history_entry = ApplianceServiceHistory(
                item_id=record.id,
                owner_key=owner_key,
                event_type="note",
                event_date=datetime.utcnow().date(),
                description="Item added to inventory.",
            )
            db.add(history_entry)
            db.commit()
            db.refresh(record)

            return InventoryItemResponse.model_validate(record)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Database error while creating item.") from exc


@router.patch("/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(
    item_id: int,
    payload: InventoryItemUpdate,
    x_homeops_user_key: str = Header(None),
):
    owner_key = _owner_key_from_header(x_homeops_user_key)
    with SessionLocal() as db:
        record = (
            db.query(InventoryItemRecord)
            .filter(InventoryItemRecord.id == item_id, InventoryItemRecord.owner_key == owner_key)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Item not found.")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(record)
        return InventoryItemResponse.model_validate(record)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(item_id: int, x_homeops_user_key: str = Header(None)):
    owner_key = _owner_key_from_header(x_homeops_user_key)
    with SessionLocal() as db:
        record = (
            db.query(InventoryItemRecord)
            .filter(InventoryItemRecord.id == item_id, InventoryItemRecord.owner_key == owner_key)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Item not found.")
        db.delete(record)
        db.commit()


# ---------------------------------------------------------------------------
# Service history
# ---------------------------------------------------------------------------

@router.get("/{item_id}/history", response_model=list[ServiceHistoryResponse])
def get_item_history(item_id: int, x_homeops_user_key: str = Header(None)):
    owner_key = _owner_key_from_header(x_homeops_user_key)
    with SessionLocal() as db:
        record = (
            db.query(InventoryItemRecord)
            .filter(InventoryItemRecord.id == item_id, InventoryItemRecord.owner_key == owner_key)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Item not found.")
        entries = (
            db.query(ApplianceServiceHistory)
            .filter(ApplianceServiceHistory.item_id == item_id)
            .order_by(ApplianceServiceHistory.event_date.desc())
            .all()
        )
        return [ServiceHistoryResponse.model_validate(e) for e in entries]


@router.post("/{item_id}/history", response_model=ServiceHistoryResponse, status_code=status.HTTP_201_CREATED)
def add_history_entry(
    item_id: int,
    payload: ServiceHistoryCreate,
    x_homeops_user_key: str = Header(None),
):
    owner_key = _owner_key_from_header(x_homeops_user_key)
    with SessionLocal() as db:
        record = (
            db.query(InventoryItemRecord)
            .filter(InventoryItemRecord.id == item_id, InventoryItemRecord.owner_key == owner_key)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Item not found.")

        entry = ApplianceServiceHistory(
            item_id=item_id,
            owner_key=owner_key,
            event_type=payload.event_type,
            event_date=payload.event_date,
            description=payload.description,
            technician=payload.technician,
            cost=payload.cost,
        )
        db.add(entry)

        # also update last_serviced on the parent item
        if payload.event_type in ("serviced", "repaired", "inspected", "replaced"):
            record.last_serviced = payload.event_date
            record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(entry)
        return ServiceHistoryResponse.model_validate(entry)
