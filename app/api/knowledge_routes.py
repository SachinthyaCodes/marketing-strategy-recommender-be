import logging
import threading

from fastapi import APIRouter, HTTPException

from app.models.knowledge_model import KnowledgeEntry
from app.services.knowledge_service import add_knowledge_entry
from app.services.realtime_service import process_realtime_updates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Base"])


def _run_realtime_updates_background() -> None:
    """Run realtime drift checks in a background thread so the knowledge
    ingestion response is not delayed by LLM calls."""
    try:
        result = process_realtime_updates()
        logger.info(
            "Background realtime update complete: checked=%d, refreshed=%d",
            result["checked"], result["refreshed"],
        )
    except Exception as exc:
        logger.error("Background realtime update failed: %s", exc)


@router.post(
    "/add",
    summary="Add a knowledge base entry",
    description="Ingest a piece of marketing knowledge with auto-generated embeddings.",
)
async def add_knowledge_endpoint(entry: KnowledgeEntry) -> dict:
    """Add a new entry to the knowledge base with its embedding.

    After successful ingestion, triggers drift detection for all
    realtime-enabled strategies in a background thread.
    """
    try:
        result = add_knowledge_entry(
            content=entry.content,
            source_type=entry.source_type,
            platform=entry.platform,
            industry=entry.industry,
        )

        # Post-ingest hook: check drift for realtime-enabled strategies
        thread = threading.Thread(
            target=_run_realtime_updates_background,
            daemon=True,
        )
        thread.start()

        return {"status": "success", "data": result}
    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Service error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        raise HTTPException(
            status_code=500, detail="Internal server error"
        ) from exc
