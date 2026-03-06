import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.ai_core.embedding_engine import generate_embedding
from app.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievalResult:
    """Container for RAG retrieval output."""

    documents: list[str]
    similarity_scores: list[float]
    created_dates: list[datetime] = field(default_factory=list)


class RAGEngine:
    """Retrieval-Augmented Generation engine using pgvector similarity search."""

    @staticmethod
    def retrieve_context(query: str, top_k: int = 5) -> RetrievalResult:
        """Retrieve the most relevant knowledge base entries for a query.

        Uses cosine distance via pgvector to find semantically similar
        documents in the knowledge_base table.

        Args:
            query: Natural language query to search against.
            top_k: Number of top results to return.

        Returns:
            RetrievalResult containing documents and their similarity scores.

        Raises:
            RuntimeError: If the retrieval query fails.
        """
        logger.info("RAG retrieval — query: '%s', top_k: %d", query[:80], top_k)

        query_embedding = generate_embedding(query)
        client = get_supabase_client()

        try:
            result = client.rpc(
                "match_knowledge",
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                },
            ).execute()

            if result.data:
                documents = [row["content"] for row in result.data]
                scores = [float(row.get("similarity", 0.0)) for row in result.data]
                dates: list[datetime] = []
                for row in result.data:
                    raw_date = row.get("created_at")
                    if raw_date:
                        try:
                            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                            dates.append(dt)
                        except (ValueError, TypeError):
                            dates.append(datetime.now(timezone.utc))
                    else:
                        dates.append(datetime.now(timezone.utc))
            else:
                documents = []
                scores = []
                dates = []

            logger.info("RAG retrieved %d documents.", len(documents))
            return RetrievalResult(
                documents=documents,
                similarity_scores=scores,
                created_dates=dates,
            )

        except Exception as exc:
            logger.error("RAG retrieval failed: %s", exc)
            raise RuntimeError(f"Knowledge retrieval failed: {exc}") from exc
