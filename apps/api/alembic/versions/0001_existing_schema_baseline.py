"""existing schema baseline

Revision ID: 0001_existing_schema_baseline
Revises:
Create Date: 2026-03-16 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_existing_schema_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "appliances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brand", sa.String(length=120), nullable=False),
        sa.Column("model_number", sa.String(length=120), nullable=False),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_appliances_user_id", "appliances", ["user_id"], unique=False)
    op.create_index("ix_appliances_model_number", "appliances", ["model_number"], unique=False)

    op.create_table(
        "uploads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appliance_id", sa.Integer(), sa.ForeignKey("appliances.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_uploads_user_id", "uploads", ["user_id"], unique=False)
    op.create_index("ix_uploads_appliance_id", "uploads", ["appliance_id"], unique=False)

    op.create_table(
        "manual_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("appliance_id", sa.Integer(), sa.ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("source_url", sa.String(length=600), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_manual_documents_appliance_id", "manual_documents", ["appliance_id"], unique=False)

    op.create_table(
        "manual_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("manual_id", sa.Integer(), sa.ForeignKey("manual_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appliance_id", sa.Integer(), sa.ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_manual_chunks_manual_id", "manual_chunks", ["manual_id"], unique=False)
    op.create_index("ix_manual_chunks_appliance_id", "manual_chunks", ["appliance_id"], unique=False)

    op.create_table(
        "diagnoses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appliance_id", sa.Integer(), sa.ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_text", sa.Text(), nullable=False),
        sa.Column("response_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_diagnoses_user_id", "diagnoses", ["user_id"], unique=False)
    op.create_index("ix_diagnoses_appliance_id", "diagnoses", ["appliance_id"], unique=False)

    op.create_table(
        "safety_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appliance_id", sa.Integer(), sa.ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("danger_level", sa.String(length=16), nullable=False),
        sa.Column("warranty_blocked", sa.Boolean(), nullable=False),
        sa.Column("software_lock_warning", sa.String(length=400), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_safety_events_user_id", "safety_events", ["user_id"], unique=False)
    op.create_index("ix_safety_events_appliance_id", "safety_events", ["appliance_id"], unique=False)

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appliance_id", sa.Integer(), sa.ForeignKey("appliances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reminder_type", sa.String(length=80), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("dedupe_key", name="uq_reminder_dedupe_key"),
    )
    op.create_index("ix_reminders_user_id", "reminders", ["user_id"], unique=False)
    op.create_index("ix_reminders_appliance_id", "reminders", ["appliance_id"], unique=False)
    op.create_index("ix_reminders_due_at", "reminders", ["due_at"], unique=False)

    op.create_table(
        "tool_handoffs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appliance_id", sa.Integer(), sa.ForeignKey("appliances.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tool_name", sa.String(length=80), nullable=False),
        sa.Column("request_payload", sa.Text(), nullable=False),
        sa.Column("response_payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tool_handoffs_user_id", "tool_handoffs", ["user_id"], unique=False)
    op.create_index("ix_tool_handoffs_appliance_id", "tool_handoffs", ["appliance_id"], unique=False)

    op.create_table(
        "alert_notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_key", sa.String(length=120), nullable=False),
        sa.Column("dedupe_key", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("time_label", sa.String(length=60), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("owner_key", "dedupe_key", name="uq_alert_owner_dedupe"),
    )
    op.create_index("ix_alert_notifications_owner_key", "alert_notifications", ["owner_key"], unique=False)

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("model_number", sa.String(length=120), nullable=False),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.Column("purchase_date", sa.String(length=40), nullable=True),
        sa.Column("last_serviced", sa.String(length=80), nullable=True),
        sa.Column("next_maintenance", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("health", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_inventory_items_owner_key", "inventory_items", ["owner_key"], unique=False)

    op.create_table(
        "appliance_service_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_key", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("event_date", sa.String(length=40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("technician", sa.String(length=120), nullable=True),
        sa.Column("cost", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_appliance_service_history_item_id", "appliance_service_history", ["item_id"], unique=False)
    op.create_index("ix_appliance_service_history_owner_key", "appliance_service_history", ["owner_key"], unique=False)

    op.create_table(
        "scan_diagnosis_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_key", sa.String(length=120), nullable=False),
        sa.Column("inventory_item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("issue_text", sa.Text(), nullable=False),
        sa.Column("extraction_json", sa.Text(), nullable=False),
        sa.Column("diagnosis_json", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_scan_diagnosis_events_owner_key", "scan_diagnosis_events", ["owner_key"], unique=False)
    op.create_index("ix_scan_diagnosis_events_inventory_item_id", "scan_diagnosis_events", ["inventory_item_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_scan_diagnosis_events_inventory_item_id", table_name="scan_diagnosis_events")
    op.drop_index("ix_scan_diagnosis_events_owner_key", table_name="scan_diagnosis_events")
    op.drop_table("scan_diagnosis_events")

    op.drop_index("ix_appliance_service_history_owner_key", table_name="appliance_service_history")
    op.drop_index("ix_appliance_service_history_item_id", table_name="appliance_service_history")
    op.drop_table("appliance_service_history")

    op.drop_index("ix_inventory_items_owner_key", table_name="inventory_items")
    op.drop_table("inventory_items")

    op.drop_index("ix_alert_notifications_owner_key", table_name="alert_notifications")
    op.drop_table("alert_notifications")

    op.drop_index("ix_tool_handoffs_appliance_id", table_name="tool_handoffs")
    op.drop_index("ix_tool_handoffs_user_id", table_name="tool_handoffs")
    op.drop_table("tool_handoffs")

    op.drop_index("ix_reminders_due_at", table_name="reminders")
    op.drop_index("ix_reminders_appliance_id", table_name="reminders")
    op.drop_index("ix_reminders_user_id", table_name="reminders")
    op.drop_table("reminders")

    op.drop_index("ix_safety_events_appliance_id", table_name="safety_events")
    op.drop_index("ix_safety_events_user_id", table_name="safety_events")
    op.drop_table("safety_events")

    op.drop_index("ix_diagnoses_appliance_id", table_name="diagnoses")
    op.drop_index("ix_diagnoses_user_id", table_name="diagnoses")
    op.drop_table("diagnoses")

    op.drop_index("ix_manual_chunks_appliance_id", table_name="manual_chunks")
    op.drop_index("ix_manual_chunks_manual_id", table_name="manual_chunks")
    op.drop_table("manual_chunks")

    op.drop_index("ix_manual_documents_appliance_id", table_name="manual_documents")
    op.drop_table("manual_documents")

    op.drop_index("ix_uploads_appliance_id", table_name="uploads")
    op.drop_index("ix_uploads_user_id", table_name="uploads")
    op.drop_table("uploads")

    op.drop_index("ix_appliances_model_number", table_name="appliances")
    op.drop_index("ix_appliances_user_id", table_name="appliances")
    op.drop_table("appliances")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")