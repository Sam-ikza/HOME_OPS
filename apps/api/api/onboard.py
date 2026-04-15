from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from auth.deps import get_current_user
from database.db import get_db
from database.models import Appliance, Upload, User
from rag.ingestion import ingest_manual_bytes, ingest_manual_url
from safety.policy import compute_warranty_active
from schemas.onboarding import ApplianceResponse, ManualIngestResponse, ManualUrlIngestRequest, OCRExtraction
from services.manual_fetcher import fetch_manual_url
from apis.vision_api import extract_appliance_details

router = APIRouter(prefix="/api/onboard", tags=["onboard"])


@router.post("/image", response_model=OCRExtraction)
async def onboard_image(
    file: UploadFile = File(...),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Onboarding image must be an image file")

    image_bytes = await file.read()
    result = extract_appliance_details(image_bytes=image_bytes, mime_type=file.content_type or "image/jpeg")
    extraction = OCRExtraction.model_validate(result)

    appliance = Appliance(
        user_id=current_user.id,
        brand=extraction.brand,
        model_number=extraction.model_number,
        serial_number=extraction.serial_number,
        purchase_date=extraction.purchase_date,
        notes=notes,
    )
    db.add(appliance)
    db.flush()

    upload = Upload(
        user_id=current_user.id,
        appliance_id=appliance.id,
        file_name=file.filename or f"upload-{datetime.utcnow().isoformat()}",
        mime_type=file.content_type or "application/octet-stream",
        source="image_onboarding",
    )
    db.add(upload)
    db.commit()

    warranty_active = compute_warranty_active(appliance.purchase_date)
    manual_url = await fetch_manual_url(appliance.brand, appliance.model_number)

    payload = extraction.model_dump()
    payload["raw_response"] = f"manual_discovery={manual_url or 'none'}"
    payload["needs_confirmation"] = extraction.needs_confirmation or extraction.confidence < 0.75
    return OCRExtraction.model_validate(payload)


@router.get("/appliances", response_model=list[ApplianceResponse])
def list_appliances(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Appliance).filter(Appliance.user_id == current_user.id).order_by(Appliance.created_at.desc()).all()
    return [
        ApplianceResponse(
            id=row.id,
            brand=row.brand,
            model_number=row.model_number,
            serial_number=row.serial_number,
            purchase_date=row.purchase_date,
            warranty_active=compute_warranty_active(row.purchase_date),
        )
        for row in rows
    ]


@router.post("/manual-upload", response_model=ManualIngestResponse)
async def onboard_manual_upload(
    appliance_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appliance = (
        db.query(Appliance)
        .filter(Appliance.id == appliance_id)
        .filter(Appliance.user_id == current_user.id)
        .first()
    )
    if not appliance:
        raise HTTPException(status_code=404, detail="Appliance not found")

    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="Manual upload must be a PDF")

    pdf_bytes = await file.read()
    title = file.filename or f"{appliance.brand}-{appliance.model_number}-manual.pdf"
    try:
        manual_id, chunk_count = ingest_manual_bytes(
            db=db,
            appliance_id=appliance.id,
            title=title,
            pdf_bytes=pdf_bytes,
            source="user_upload",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Manual ingestion failed") from exc

    return ManualIngestResponse(manual_id=manual_id, chunk_count=chunk_count, source="user_upload")


@router.post("/manual-url", response_model=ManualIngestResponse)
async def onboard_manual_url(
    payload: ManualUrlIngestRequest,
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

    try:
        manual_id, chunk_count = await ingest_manual_url(
            db=db,
            appliance_id=appliance.id,
            source_url=payload.url,
            title=payload.title,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to ingest manual URL: {exc}") from exc

    return ManualIngestResponse(manual_id=manual_id, chunk_count=chunk_count, source="manual_url")
