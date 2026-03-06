from pydantic import BaseModel, Field


class KnowledgeEntry(BaseModel):
    """Request body for adding a knowledge base entry."""

    content: str = Field(
        ..., min_length=1, description="Text content of the knowledge entry"
    )
    source_type: str = Field(
        ..., min_length=1, description="Source category (e.g., article, case_study)"
    )
    platform: str | None = Field(
        default=None, description="Marketing platform this relates to"
    )
    industry: str | None = Field(
        default=None, description="Industry this knowledge relates to"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Instagram Reels generate 67% more engagement than standard posts for food businesses.",
                    "source_type": "research",
                    "platform": "Instagram",
                    "industry": "Food & Beverage",
                }
            ]
        }
    }
