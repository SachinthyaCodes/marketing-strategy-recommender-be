import logging

from app.ai_core.embedding_engine import generate_embedding
from app.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def add_knowledge_entry(
    content: str,
    source_type: str,
    platform: str | None = None,
    industry: str | None = None,
) -> dict:
    """Ingest a knowledge entry with its embedding into the knowledge base.

    Args:
        content: The text content to store.
        source_type: Category of the source (e.g., "article", "case_study").
        platform: Optional marketing platform this knowledge relates to.
        industry: Optional industry this knowledge relates to.

    Returns:
        The inserted record data from Supabase.

    Raises:
        ValueError: If content is empty.
        RuntimeError: If database insert fails.
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty.")

    logger.info("Generating embedding for knowledge entry (%s)", source_type)
    embedding = generate_embedding(content)

    record = {
        "content": content,
        "source_type": source_type,
        "platform": platform,
        "industry": industry,
        "embedding": embedding,
    }

    client = get_supabase_client()
    try:
        result = client.table("knowledge_base").insert(record).execute()
        logger.info("Knowledge entry stored successfully.")
        return result.data[0] if result.data else {}
    except Exception as exc:
        logger.error("Failed to store knowledge entry: %s", exc)
        raise RuntimeError(f"Knowledge base insert failed: {exc}") from exc
