"""normalize inventory date columns

Revision ID: a002_inventory_dates
Revises: 0001_existing_schema_baseline
Create Date: 2026-03-16 00:10:00
"""

from __future__ import annotations

from datetime import date, datetime

from alembic import op
import sqlalchemy as sa


revision = "a002_inventory_dates"
down_revision = "0001_existing_schema_baseline"
branch_labels = None
depends_on = None


def _parse_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value

    raw = str(value).strip()
    if not raw:
        return None

    normalized = raw.lower()
    if normalized in {"unknown", "n/a", "na", "today", "not serviced yet"}:
        return None

    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%b %Y", "%B %Y"):
        try:
            parsed = datetime.strptime(raw, pattern)
            if pattern in {"%b %Y", "%B %Y"}:
                return date(parsed.year, parsed.month, 1)
            return parsed.date()
        except ValueError:
            continue

    return None


def _format_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column("inventory_items", sa.Column("purchase_date_tmp", sa.Date(), nullable=True))
    op.add_column("inventory_items", sa.Column("last_serviced_tmp", sa.Date(), nullable=True))
    op.add_column("appliance_service_history", sa.Column("event_date_tmp", sa.Date(), nullable=True))

    inventory_items = sa.table(
        "inventory_items",
        sa.column("id", sa.Integer()),
        sa.column("purchase_date", sa.String()),
        sa.column("last_serviced", sa.String()),
        sa.column("purchase_date_tmp", sa.Date()),
        sa.column("last_serviced_tmp", sa.Date()),
    )
    service_history = sa.table(
        "appliance_service_history",
        sa.column("id", sa.Integer()),
        sa.column("event_date", sa.String()),
        sa.column("event_date_tmp", sa.Date()),
    )

    inventory_rows = bind.execute(
        sa.select(inventory_items.c.id, inventory_items.c.purchase_date, inventory_items.c.last_serviced)
    ).mappings()
    for row in inventory_rows:
        bind.execute(
            sa.update(inventory_items)
            .where(inventory_items.c.id == row["id"])
            .values(
                purchase_date_tmp=_parse_date(row["purchase_date"]),
                last_serviced_tmp=_parse_date(row["last_serviced"]),
            )
        )

    history_rows = bind.execute(sa.select(service_history.c.id, service_history.c.event_date)).mappings()
    for row in history_rows:
        bind.execute(
            sa.update(service_history)
            .where(service_history.c.id == row["id"])
            .values(event_date_tmp=_parse_date(row["event_date"]))
        )

    with op.batch_alter_table("inventory_items") as batch_op:
        batch_op.drop_column("purchase_date")
        batch_op.drop_column("last_serviced")
        batch_op.alter_column(
            "purchase_date_tmp",
            existing_type=sa.Date(),
            existing_nullable=True,
            new_column_name="purchase_date",
        )
        batch_op.alter_column(
            "last_serviced_tmp",
            existing_type=sa.Date(),
            existing_nullable=True,
            new_column_name="last_serviced",
        )

    with op.batch_alter_table("appliance_service_history") as batch_op:
        batch_op.drop_column("event_date")
        batch_op.alter_column(
            "event_date_tmp",
            existing_type=sa.Date(),
            existing_nullable=True,
            nullable=False,
            new_column_name="event_date",
        )


def downgrade() -> None:
    bind = op.get_bind()

    op.add_column("inventory_items", sa.Column("purchase_date_text", sa.String(length=40), nullable=True))
    op.add_column("inventory_items", sa.Column("last_serviced_text", sa.String(length=80), nullable=True))
    op.add_column("appliance_service_history", sa.Column("event_date_text", sa.String(length=40), nullable=True))

    inventory_items = sa.table(
        "inventory_items",
        sa.column("id", sa.Integer()),
        sa.column("purchase_date", sa.Date()),
        sa.column("last_serviced", sa.Date()),
        sa.column("purchase_date_text", sa.String()),
        sa.column("last_serviced_text", sa.String()),
    )
    service_history = sa.table(
        "appliance_service_history",
        sa.column("id", sa.Integer()),
        sa.column("event_date", sa.Date()),
        sa.column("event_date_text", sa.String()),
    )

    inventory_rows = bind.execute(
        sa.select(inventory_items.c.id, inventory_items.c.purchase_date, inventory_items.c.last_serviced)
    ).mappings()
    for row in inventory_rows:
        bind.execute(
            sa.update(inventory_items)
            .where(inventory_items.c.id == row["id"])
            .values(
                purchase_date_text=_format_date(row["purchase_date"]),
                last_serviced_text=_format_date(row["last_serviced"]),
            )
        )

    history_rows = bind.execute(sa.select(service_history.c.id, service_history.c.event_date)).mappings()
    for row in history_rows:
        bind.execute(
            sa.update(service_history)
            .where(service_history.c.id == row["id"])
            .values(event_date_text=_format_date(row["event_date"]))
        )

    with op.batch_alter_table("inventory_items") as batch_op:
        batch_op.drop_column("purchase_date")
        batch_op.drop_column("last_serviced")
        batch_op.alter_column(
            "purchase_date_text",
            existing_type=sa.String(length=40),
            existing_nullable=True,
            new_column_name="purchase_date",
        )
        batch_op.alter_column(
            "last_serviced_text",
            existing_type=sa.String(length=80),
            existing_nullable=True,
            new_column_name="last_serviced",
        )

    with op.batch_alter_table("appliance_service_history") as batch_op:
        batch_op.drop_column("event_date")
        batch_op.alter_column(
            "event_date_text",
            existing_type=sa.String(length=40),
            existing_nullable=True,
            nullable=False,
            new_column_name="event_date",
        )