import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from apis.llm_api import generate_diagnosis_json
from apis.vision_api import analyze_appliance_scene, match_demo_appliance_scene
from auth.deps import get_current_user
from database.db import get_db
from database.models import Appliance, Diagnosis, InventoryItemRecord, SafetyEvent, ScanDiagnosisEvent, User
from rag.vector_store import query_manual_chunks
from safety.policy import compute_warranty_active, enforce_business_rules
from schemas.diagnosis import (
    DiagnosisRequest,
    DiagnosisResponse,
    ImageDiagnosisExtraction,
    ImageDiagnosisHistoryItem,
    ImageDiagnosisResponse,
)

router = APIRouter(prefix="/api/diagnose", tags=["diagnose"])


class DiagnoseMockRequest(BaseModel):
    brand: str = "Unknown"
    model_number: str = "Unknown"
    issue_text: str = Field(min_length=3)
    purchase_date: date | None = None


def _owner_key_from_header(x_homeops_user_key: str | None = Header(default=None, alias="X-HomeOps-User-Key")) -> str:
    candidate = (x_homeops_user_key or "").strip()
    if len(candidate) < 8 or len(candidate) > 120:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing or invalid X-HomeOps-User-Key")
    return candidate


def _parse_inventory_purchase_date(purchase_date: date | str | None) -> date | None:
    if not purchase_date:
        return None
    if isinstance(purchase_date, date):
        return purchase_date

    raw = purchase_date.strip()
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%b %Y", "%B %Y"):
        try:
            parsed = datetime.strptime(raw, pattern)
            if pattern in ("%b %Y", "%B %Y"):
                return date(parsed.year, parsed.month, 1)
            return parsed.date()
        except ValueError:
            continue
    return None


def _has_severe_visual_risk(extraction: ImageDiagnosisExtraction) -> bool:
    merged = " ".join(
        [
            extraction.likely_issue,
            extraction.summary or "",
            extraction.display_text or "",
            " ".join(extraction.visible_signals),
            " ".join(extraction.risk_flags),
        ]
    ).lower()
    severe_terms = {
        "spark",
        "sparks",
        "smoke",
        "burn",
        "burnt",
        "flame",
        "gas leak",
        "refrigerant leak",
        "exposed wire",
        "leak near electrical",
    }
    return any(term in merged for term in severe_terms)


def _build_scan_chat_prompt(extraction: ImageDiagnosisExtraction, diagnosis: DiagnosisResponse, issue_text: str) -> str:
    return " ".join(
        [
            "Help me troubleshoot this appliance based on image analysis.",
            f"Observed issue: {issue_text}.",
            f"Detected appliance: {extraction.brand} {extraction.model_number}.",
            f"Likely visible issue: {extraction.likely_issue}.",
            f"Error code seen: {extraction.error_code or 'none'}.",
            f"Visible signals: {', '.join(extraction.visible_signals) if extraction.visible_signals else 'none'}.",
            f"Risk flags: {', '.join(extraction.risk_flags) if extraction.risk_flags else 'none'}.",
            f"Current diagnosis summary: {diagnosis.diagnosis_summary}.",
            "Give a concise safety-first step-by-step plan and what to verify next.",
        ]
    )


def _safe_image_diagnosis_fallback(issue_text: str, warranty_active: bool) -> DiagnosisResponse:
    return DiagnosisResponse(
        danger_level="LOW",
        call_pro=False,
        warranty_active=warranty_active,
        warranty_block_reason=("Appliance appears to be under active warranty window." if warranty_active else None),
        manufacturer_support=(
            "Contact manufacturer support with serial/model for authorized service."
            if warranty_active
            else None
        ),
        fragility_warning="Handle plastic clips, glass, and sensor connectors gently to avoid breakage.",
        physical_brief={
            "estimated_time_minutes": 15,
            "heavy_lifting_required": False,
            "estimated_weight_lbs": 0,
            "spill_risk": "LOW",
        },
        software_lock_warning=None,
        diagnosis_summary="Visual analysis completed, but confidence is limited. Start with basic external checks.",
        diy_steps=(
            []
            if warranty_active
            else [
                "Ensure the appliance is connected to power and the wall switch is ON.",
                "Check breaker/fuse and visible cables for obvious disconnects.",
                "If an error code is visible, note it and retry with a clearer close-up image.",
            ]
        ),
        required_parts=[],
        citations=[],
        escalation_message=(
            "Contact manufacturer support for authorized service under warranty."
            if warranty_active
            else "If the issue persists after basic checks, contact a professional technician."
        ),
    )


@router.post("/mock", response_model=DiagnosisResponse)
def diagnose_mock(payload: DiagnoseMockRequest):
    warranty_active = compute_warranty_active(payload.purchase_date)

    response = DiagnosisResponse(
        danger_level="MEDIUM",
        call_pro=False,
        warranty_active=warranty_active,
        warranty_block_reason=None,
        manufacturer_support=None,
        fragility_warning="Handle clips and sensor connectors carefully.",
        physical_brief={
            "estimated_time_minutes": 30,
            "heavy_lifting_required": False,
            "estimated_weight_lbs": 12,
            "spill_risk": "MEDIUM",
        },
        software_lock_warning=None,
        diagnosis_summary="Mock diagnosis endpoint reachable.",
        diy_steps=[
            "Power cycle the appliance and inspect visible filter/drain paths.",
            "Capture any displayed error code for deeper diagnosis.",
        ],
        required_parts=[],
        citations=[{"source": "mock", "snippet": "Connectivity test response"}],
        escalation_message="Escalate to a pro if burning smell, sparks, or gas odor is present.",
    )

    return enforce_business_rules(
        response=response,
        issue_text=payload.issue_text,
        warranty_active=warranty_active,
        model_text=f"{payload.brand} {payload.model_number}",
    )


@router.post("", response_model=DiagnosisResponse)
def diagnose(
    payload: DiagnosisRequest,
    request: Request,
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

    warranty_active = compute_warranty_active(appliance.purchase_date)
    contexts = query_manual_chunks(
        db=db,
        appliance_id=appliance.id,
        query_text=payload.issue_text,
        top_k=5,
    )

    llm_payload = generate_diagnosis_json(
        issue_text=payload.issue_text,
        manual_chunks=contexts,
        appliance_brand=appliance.brand,
        appliance_model=appliance.model_number,
        warranty_active=warranty_active,
    )

    try:
        diagnosis = DiagnosisResponse.model_validate(llm_payload)
    except Exception:
        diagnosis = _safe_image_diagnosis_fallback(
            issue_text=payload.issue_text,
            warranty_active=warranty_active,
        )

    diagnosis = enforce_business_rules(
        response=diagnosis,
        issue_text=payload.issue_text,
        warranty_active=warranty_active,
        model_text=f"{appliance.brand} {appliance.model_number}",
    )

    db_record = Diagnosis(
        user_id=current_user.id,
        appliance_id=appliance.id,
        issue_text=payload.issue_text,
        response_json=json.dumps(diagnosis.model_dump()),
    )
    db.add(db_record)

    safety_event = SafetyEvent(
        user_id=current_user.id,
        appliance_id=appliance.id,
        danger_level=diagnosis.danger_level,
        warranty_blocked=diagnosis.warranty_active,
        software_lock_warning=diagnosis.software_lock_warning,
        reason=diagnosis.escalation_message,
    )
    db.add(safety_event)
    db.commit()

    request.state.model_used = llm_payload.get("_model", "fallback") if isinstance(llm_payload, dict) else "fallback"
    return diagnosis


@router.post("/from-image", response_model=ImageDiagnosisResponse)
async def diagnose_from_image(
    request: Request,
    file: UploadFile = File(...),
    issue_text: str = Form(default=""),
    inventory_item_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    owner_key: str = Depends(_owner_key_from_header),
):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Image diagnosis requires an image file")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image payload")

    inventory_item: InventoryItemRecord | None = None
    if inventory_item_id is not None:
        inventory_item = (
            db.query(InventoryItemRecord)
            .filter(InventoryItemRecord.id == inventory_item_id)
            .filter(InventoryItemRecord.owner_key == owner_key)
            .first()
        )
        if not inventory_item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

    extraction_payload = match_demo_appliance_scene(file.filename)
    if not extraction_payload:
        extraction_payload = analyze_appliance_scene(
            image_bytes=image_bytes,
            mime_type=file.content_type or "image/jpeg",
            issue_text=issue_text,
        )
    extraction = ImageDiagnosisExtraction.model_validate(extraction_payload)

    brand = extraction.brand
    model_number = extraction.model_number
    warranty_active = False
    if inventory_item:
        brand = inventory_item.brand or brand
        model_number = inventory_item.model_number or model_number
        warranty_active = compute_warranty_active(_parse_inventory_purchase_date(inventory_item.purchase_date))

    effective_issue_parts = [
        issue_text.strip(),
        extraction.likely_issue,
        f"Error code: {extraction.error_code}" if extraction.error_code else "",
        f"Visible signals: {', '.join(extraction.visible_signals)}" if extraction.visible_signals else "",
    ]
    effective_issue_text = " ".join(part for part in effective_issue_parts if part).strip() or "Appliance not working"

    image_context = {
        "error_code": extraction.error_code,
        "display_text": extraction.display_text,
        "likely_issue": extraction.likely_issue,
        "visible_signals": extraction.visible_signals,
        "risk_flags": extraction.risk_flags,
        "confidence": extraction.confidence,
        "summary": extraction.summary,
    }

    llm_payload = generate_diagnosis_json(
        issue_text=effective_issue_text,
        manual_chunks=[],
        appliance_brand=brand,
        appliance_model=model_number,
        warranty_active=warranty_active,
        image_context=image_context,
    )

    try:
        diagnosis = DiagnosisResponse.model_validate(llm_payload)
    except Exception:
        diagnosis = _safe_image_diagnosis_fallback(
            issue_text=effective_issue_text,
            warranty_active=warranty_active,
        )

    diagnosis = enforce_business_rules(
        response=diagnosis,
        issue_text=effective_issue_text,
        warranty_active=warranty_active,
        model_text=f"{brand} {model_number}",
    )

    if _has_severe_visual_risk(extraction):
        diagnosis.danger_level = "HIGH"
        diagnosis.call_pro = True
        diagnosis.diy_steps = []
        diagnosis.escalation_message = (
            "Potentially dangerous visual signs detected. Turn off power/gas/water as applicable and contact a professional immediately."
        )

    event_id: int | None = None
    try:
        event = ScanDiagnosisEvent(
            owner_key=owner_key,
            inventory_item_id=inventory_item.id if inventory_item else None,
            issue_text=effective_issue_text,
            extraction_json=json.dumps(extraction.model_dump()),
            diagnosis_json=json.dumps(diagnosis.model_dump()),
            source=extraction.source,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id
    except SQLAlchemyError:
        # Diagnosis should still succeed even if optional history persistence fails.
        db.rollback()

    request.state.model_used = llm_payload.get("_model", "fallback") if isinstance(llm_payload, dict) else "fallback"
    return ImageDiagnosisResponse(
        extraction=extraction,
        diagnosis=diagnosis,
        chat_prompt=_build_scan_chat_prompt(extraction=extraction, diagnosis=diagnosis, issue_text=effective_issue_text),
        event_id=event_id,
    )


@router.get("/from-image/history", response_model=list[ImageDiagnosisHistoryItem])
def list_image_diagnosis_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    owner_key: str = Depends(_owner_key_from_header),
):
    safe_limit = max(1, min(limit, 100))
    rows = (
        db.query(ScanDiagnosisEvent)
        .filter(ScanDiagnosisEvent.owner_key == owner_key)
        .order_by(ScanDiagnosisEvent.created_at.desc())
        .limit(safe_limit)
        .all()
    )

    items: list[ImageDiagnosisHistoryItem] = []
    for row in rows:
        try:
            extraction = ImageDiagnosisExtraction.model_validate(json.loads(row.extraction_json))
            diagnosis = DiagnosisResponse.model_validate(json.loads(row.diagnosis_json))
        except Exception:
            continue
        items.append(
            ImageDiagnosisHistoryItem(
                id=row.id,
                inventory_item_id=row.inventory_item_id,
                issue_text=row.issue_text,
                extraction=extraction,
                diagnosis=diagnosis,
                created_at=row.created_at,
            )
        )

    return items
