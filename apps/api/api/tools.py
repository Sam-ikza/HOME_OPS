import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.deps import get_current_user
from config import settings
from database.db import get_db
from database.models import Appliance, ToolHandoff, User
from schemas.tools import PartsLinkRequest, ProHandoffRequest, ToolResponse
from tools.providers import build_affiliate_links, draft_pro_handoff

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.post("/pro-handoff", response_model=ToolResponse)
def pro_handoff(
    payload: ProHandoffRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.tool_calls_enabled:
        raise HTTPException(status_code=403, detail="Tool calls are disabled")

    appliance = (
        db.query(Appliance)
        .filter(Appliance.id == payload.appliance_id)
        .filter(Appliance.user_id == current_user.id)
        .first()
    )
    if not appliance:
        raise HTTPException(status_code=404, detail="Appliance not found")

    result = draft_pro_handoff(
        appliance={
            "brand": appliance.brand,
            "model_number": appliance.model_number,
            "serial_number": appliance.serial_number,
        },
        issue_summary=payload.issue_summary,
        city=payload.city,
    )

    record = ToolHandoff(
        user_id=current_user.id,
        appliance_id=appliance.id,
        tool_name="pro_handoff",
        request_payload=payload.model_dump_json(),
        response_payload=json.dumps(result),
    )
    db.add(record)
    db.commit()

    return ToolResponse(tool_name="pro_handoff", payload=result)


@router.post("/parts-links", response_model=ToolResponse)
def parts_links(
    payload: PartsLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.tool_calls_enabled:
        raise HTTPException(status_code=403, detail="Tool calls are disabled")

    appliance = (
        db.query(Appliance)
        .filter(Appliance.id == payload.appliance_id)
        .filter(Appliance.user_id == current_user.id)
        .first()
    )
    if not appliance:
        raise HTTPException(status_code=404, detail="Appliance not found")

    result = build_affiliate_links(
        appliance={"brand": appliance.brand, "model_number": appliance.model_number},
        part_query=payload.part_query,
    )

    record = ToolHandoff(
        user_id=current_user.id,
        appliance_id=appliance.id,
        tool_name="parts_links",
        request_payload=payload.model_dump_json(),
        response_payload=json.dumps(result),
    )
    db.add(record)
    db.commit()

    return ToolResponse(tool_name="parts_links", payload=result)
