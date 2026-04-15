from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.deps import get_current_user
from database.db import get_db
from database.models import Appliance, ManualDocument, User

router = APIRouter(prefix="/api/manuals", tags=["manuals"])


@router.get("/{appliance_id}")
def list_manuals(
    appliance_id: int,
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
        return {"manuals": []}

    docs = db.query(ManualDocument).filter(ManualDocument.appliance_id == appliance_id).all()
    return {
        "manuals": [
            {
                "id": doc.id,
                "title": doc.title,
                "source": doc.source,
                "source_url": doc.source_url,
                "created_at": doc.created_at,
            }
            for doc in docs
        ]
    }
