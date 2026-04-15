from __future__ import annotations

import json
from io import BytesIO

import httpx
from pypdf import PdfReader
from sqlalchemy.orm import Session

from database.models import ManualChunk, ManualDocument
from rag.vector_store import upsert_chunks


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    clean = " ".join(text.split())
    if not clean:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + chunk_size)
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise ValueError("Unable to read PDF file") from exc

    text_parts: list[str] = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def ingest_manual_bytes(
    db: Session,
    appliance_id: int,
    title: str,
    pdf_bytes: bytes,
    source: str,
    source_url: str | None = None,
) -> tuple[int, int]:
    full_text = _extract_pdf_text(pdf_bytes)
    chunks = _chunk_text(full_text)

    if not chunks:
        raise ValueError("PDF did not contain extractable manual text")

    manual = ManualDocument(
        appliance_id=appliance_id,
        title=title,
        source=source,
        source_url=source_url,
    )

    try:
        db.add(manual)
        db.flush()

        chunk_rows: list[ManualChunk] = []
        metadatas: list[dict] = []

        for idx, chunk in enumerate(chunks):
            metadata = {
                "appliance_id": appliance_id,
                "manual_id": manual.id,
                "chunk_index": idx,
                "source": source,
            }
            row = ManualChunk(
                manual_id=manual.id,
                appliance_id=appliance_id,
                chunk_index=idx,
                text=chunk,
                metadata_json=json.dumps(metadata),
            )
            chunk_rows.append(row)
            metadatas.append(metadata)

        if chunk_rows:
            db.add_all(chunk_rows)

        db.commit()
    except Exception:
        db.rollback()
        raise

    if chunks:
        upsert_chunks(documents=chunks, metadatas=metadatas)

    return manual.id, len(chunks)


async def ingest_manual_url(
    db: Session,
    appliance_id: int,
    source_url: str,
    title: str | None = None,
) -> tuple[int, int]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(source_url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "pdf" not in content_type.lower() and not source_url.lower().endswith(".pdf"):
            raise ValueError("Provided URL does not look like a PDF manual")

    inferred_title = title or source_url.rstrip("/").split("/")[-1] or "manual.pdf"
    return ingest_manual_bytes(
        db=db,
        appliance_id=appliance_id,
        title=inferred_title,
        pdf_bytes=response.content,
        source="manual_url",
        source_url=source_url,
    )
