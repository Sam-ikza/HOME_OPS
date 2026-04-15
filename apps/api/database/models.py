from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    appliances: Mapped[list["Appliance"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Appliance(Base):
    __tablename__ = "appliances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(120), nullable=False)
    model_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="appliances")
    uploads: Mapped[list["Upload"]] = relationship(back_populates="appliance", cascade="all, delete-orphan")
    manuals: Mapped[list["ManualDocument"]] = relationship(back_populates="appliance", cascade="all, delete-orphan")


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appliance_id: Mapped[int | None] = mapped_column(ForeignKey("appliances.id", ondelete="SET NULL"), nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="upload")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    appliance: Mapped[Optional["Appliance"]] = relationship(back_populates="uploads")


class ManualDocument(Base):
    __tablename__ = "manual_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="upload")
    source_url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    appliance: Mapped["Appliance"] = relationship(back_populates="manuals")
    chunks: Mapped[list["ManualChunk"]] = relationship(back_populates="manual", cascade="all, delete-orphan")


class ManualChunk(Base):
    __tablename__ = "manual_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manual_id: Mapped[int] = mapped_column(ForeignKey("manual_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    manual: Mapped["ManualDocument"] = relationship(back_populates="chunks")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False, index=True)
    danger_level: Mapped[str] = mapped_column(String(16), nullable=False)
    warranty_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    software_lock_warning: Mapped[str | None] = mapped_column(String(400), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_reminder_dedupe_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appliance_id: Mapped[int] = mapped_column(ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_type: Mapped[str] = mapped_column(String(80), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ToolHandoff(Base):
    __tablename__ = "tool_handoffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appliance_id: Mapped[int | None] = mapped_column(ForeignKey("appliances.id", ondelete="SET NULL"), nullable=True, index=True)
    tool_name: Mapped[str] = mapped_column(String(80), nullable=False)
    request_payload: Mapped[str] = mapped_column(Text, nullable=False)
    response_payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AlertNotification(Base):
    __tablename__ = "alert_notifications"
    __table_args__ = (UniqueConstraint("owner_key", "dedupe_key", name="uq_alert_owner_dedupe"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dedupe_key: Mapped[str] = mapped_column(String(180), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    time_label: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="low")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Inventory (owner-key based – no JWT required, same pattern as alerts)
# ---------------------------------------------------------------------------

class InventoryItemRecord(Base):
    """Stores appliance / inventory items for a user identified by owner_key."""
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="Appliances")
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_number: Mapped[str] = mapped_column(String(120), nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_serviced: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_maintenance: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="good")
    health: Mapped[int] = mapped_column(Integer, nullable=False, default=85)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    history: Mapped[list["ApplianceServiceHistory"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ApplianceServiceHistory.event_date.desc()"
    )


class ApplianceServiceHistory(Base):
    """Tracks service / maintenance events for an inventory item."""
    __tablename__ = "appliance_service_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)   # e.g. "serviced", "repaired", "note"
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technician: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cost: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    item: Mapped["InventoryItemRecord"] = relationship(back_populates="history")


class ScanDiagnosisEvent(Base):
    """Stores image-diagnosis outputs (no raw image bytes) per owner key."""
    __tablename__ = "scan_diagnosis_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    inventory_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    issue_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    extraction_json: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis_json: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="gemini")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
