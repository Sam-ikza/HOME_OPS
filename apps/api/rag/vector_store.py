"""Vector retrieval service with Pinecone adapter and DB fallback."""

from __future__ import annotations

import hashlib
import logging
from collections import Counter

from sqlalchemy.orm import Session

from config import settings
from database.models import ManualChunk

logger = logging.getLogger(__name__)


def _pseudo_vector(text: str, dims: int = 64) -> list[float]:
    return [
        (int(hashlib.sha1(f"{text}:{i}".encode("utf-8")).hexdigest()[:6], 16) % 1000) / 1000.0
        for i in range(dims)
    ]


def _tokenize(text: str) -> list[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [token for token in cleaned.split() if len(token) > 2]


def _lexical_score(query_tokens: list[str], candidate_text: str) -> int:
    if not query_tokens:
        return 0
    bag = Counter(_tokenize(candidate_text))
    return sum(bag.get(token, 0) for token in query_tokens)


def upsert_chunks(documents: list[str], metadatas: list[dict]) -> None:
    """Best-effort vector upsert.

    In hackathon mode we always keep DB chunks as the source of truth.
    If Pinecone is configured, we additionally upsert lightweight records.
    """
    if not documents:
        return

    if not settings.pinecone_api_key or not settings.vector_provider.lower().startswith("pinecone"):
        return

    try:
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(settings.pinecone_index)
        vectors = []
        for doc, metadata in zip(documents, metadatas):
            vector_id = hashlib.sha1(f"{metadata.get('manual_id')}:{metadata.get('chunk_index')}".encode("utf-8")).hexdigest()
            # Hash-based pseudo embedding keeps ingestion cheap for hackathon demos.
            pseudo = _pseudo_vector(doc)
            vectors.append({"id": vector_id, "values": pseudo, "metadata": {**metadata, "text": doc[:500]}})

        index.upsert(vectors=vectors)
    except Exception as exc:  # pragma: no cover - external provider dependent
        logger.warning("pinecone_upsert_failed=%s", exc)


def query_manual_chunks(db: Session, appliance_id: int, query_text: str, top_k: int = 5) -> list[dict]:
    if settings.pinecone_api_key and settings.vector_provider.lower().startswith("pinecone"):
        try:
            from pinecone import Pinecone

            pc = Pinecone(api_key=settings.pinecone_api_key)
            index = pc.Index(settings.pinecone_index)
            response = index.query(
                vector=_pseudo_vector(query_text),
                top_k=top_k,
                include_metadata=True,
                filter={"appliance_id": {"$eq": appliance_id}},
            )

            matches = getattr(response, "matches", []) or []
            pinecone_results = []
            for item in matches:
                meta = item.get("metadata", {}) if isinstance(item, dict) else getattr(item, "metadata", {})
                if not meta:
                    continue
                pinecone_results.append(
                    {
                        "document": meta.get("text", ""),
                        "metadata": {
                            "manual_id": meta.get("manual_id"),
                            "chunk_id": meta.get("chunk_id"),
                            "chunk_index": meta.get("chunk_index"),
                            "source": meta.get("source", "manual"),
                        },
                    }
                )

            if pinecone_results:
                return pinecone_results
        except Exception as exc:  # pragma: no cover - provider dependent
            logger.warning("pinecone_query_failed=%s", exc)

    rows = db.query(ManualChunk).filter(ManualChunk.appliance_id == appliance_id).all()
    if not rows:
        return []

    query_tokens = _tokenize(query_text)
    ranked = sorted(rows, key=lambda row: _lexical_score(query_tokens, row.text), reverse=True)

    selected = ranked[:top_k]
    return [
        {
            "document": row.text,
            "metadata": {
                "manual_id": row.manual_id,
                "chunk_id": row.id,
                "chunk_index": row.chunk_index,
                "source": "manual",
            },
        }
        for row in selected
    ]
