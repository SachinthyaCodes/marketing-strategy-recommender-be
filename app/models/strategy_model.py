from pydantic import BaseModel, Field


class MarketingStrategy(BaseModel):
    """Structured marketing strategy output from the AI engine."""

    strategy_summary: str = Field(
        ..., min_length=1, description="High-level strategy overview"
    )
    recommended_platforms: list[str] = Field(
        ..., min_length=1, description="Platforms recommended for marketing"
    )
    content_strategy: str = Field(
        ..., min_length=1, description="Content creation and distribution plan"
    )
    budget_allocation: dict[str, float] = Field(
        ..., description="Budget split across channels (channel -> percentage)"
    )
    reasoning: str = Field(
        ..., min_length=1, description="Rationale behind the strategy"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Mathematical confidence of the recommendation"
    )
    version: int = Field(
        default=1, ge=1, description="Strategy version number"
    )
    is_outdated: bool = Field(
        default=False, description="Whether the strategy has drifted from current context"
    )

    # ── Phase 5: Advanced confidence breakdown (research visibility) ──
    trend_recency_score: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Freshness score of retrieved knowledge documents",
    )
    similarity_score: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Average cosine similarity from RAG retrieval",
    )
    data_coverage_score: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Ratio of documents retrieved vs. requested (top_k)",
    )
    platform_stability_score: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Stability heuristic based on recommended platform count",
    )

    # ── Phase 6: Drift detection metadata ────────────────────────────
    drift_similarity: float | None = Field(
        default=None, ge=-1.0, le=1.0,
        description="Cosine similarity between stored strategy and latest context embedding",
    )
    drift_level: str | None = Field(
        default=None,
        description="Semantic drift classification: LOW, MODERATE, or HIGH",
    )
    regenerate_flag: bool | None = Field(
        default=None,
        description="Whether drift analysis determined regeneration was required",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategy_summary": "Focus on social-first organic growth with targeted paid ads.",
                    "recommended_platforms": ["Instagram", "Facebook"],
                    "content_strategy": "Post 3x/week with mix of reels, stories, and carousels.",
                    "budget_allocation": {
                        "Instagram Ads": 40.0,
                        "Facebook Ads": 30.0,
                        "Content Creation": 20.0,
                        "Influencer Partnerships": 10.0,
                    },
                    "reasoning": "Target audience is highly active on Instagram and Facebook.",
                    "confidence_score": 0.85,
                    "version": 1,
                    "is_outdated": False,
                    "trend_recency_score": 0.82,
                    "similarity_score": 0.76,
                    "data_coverage_score": 0.80,
                    "platform_stability_score": 1.0,
                    "drift_similarity": 0.91,
                    "drift_level": "LOW",
                    "regenerate_flag": False,
                }
            ]
        }
    }
