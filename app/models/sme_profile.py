from typing import Any, Union

from pydantic import BaseModel, Field, field_validator


class LocationInfo(BaseModel):
    """Geographic location of the business."""

    city: str = Field(..., min_length=1, max_length=200)
    district: str | None = Field(default=None, max_length=200)
    country: str | None = Field(default=None, max_length=200)


class Demographics(BaseModel):
    """Target audience demographic breakdown."""

    age_range: str = Field(..., description="Primary age bracket")
    gender: list[str] = Field(..., min_length=1, description="Target genders")
    income_level: str = Field(..., description="Income bracket")
    education_level: str | None = Field(default=None, description="Education level of target audience")


class BrandAssets(BaseModel):
    """Existing brand collateral."""

    has_logo: bool = False
    has_brand_style: bool = False
    brand_colors: list[str] = Field(default_factory=list)


class SeasonalityEntry(BaseModel):
    """A seasonal factor affecting the business."""

    category: str
    subcategories: list[str] = Field(default_factory=list)


class SMEProfile(BaseModel):
    """Comprehensive SME profile matching the multi-step frontend form."""

    # --- Section 1: Business Profile ---
    business_type: str = Field(..., description="Business category")
    industry: str | None = Field(default=None, max_length=200, description="Specific industry niche")
    business_size: str = Field(..., description="Team size tier: solo | small-team | medium | large")
    business_stage: str = Field(..., description="Maturity: new | growing | established")
    location: LocationInfo
    products_services: str = Field(..., min_length=1, description="Products or services offered")
    unique_selling_proposition: str = Field(..., min_length=1, description="USP / competitive edge")

    # --- Section 2: Budget & Resources ---
    monthly_budget: Union[str, int, float] = Field(..., description="Budget amount or range label")
    has_marketing_team: bool = Field(default=False)
    team_size: int | None = Field(default=None, ge=1, le=100)
    content_creation_capacity: list[str] = Field(default_factory=list)

    @field_validator("monthly_budget", mode="before")
    @classmethod
    def coerce_budget_to_str(cls, v: Any) -> str:
        """Accept numeric budgets and convert to string for prompt use."""
        return str(v)

    # --- Section 3: Goals ---
    primary_goal: str = Field(..., description="Primary marketing objective")
    secondary_goals: list[str] = Field(default_factory=list)
    target_revenue_increase: int | float | None = Field(default=None, description="Target revenue increase percentage")
    timeline: str | None = Field(default=None, description="Goal timeline")

    # --- Section 4: Target Audience ---
    demographics: Demographics
    target_location: str = Field(..., min_length=1, description="Geographic target")
    interests: list[str] = Field(default_factory=list)
    buying_frequency: str = Field(..., description="rare | monthly | weekly | daily")

    # --- Section 5: Platforms & Preferences ---
    preferred_platforms: list[str] = Field(..., min_length=1)
    current_platforms: list[str] = Field(default_factory=list, description="Currently active platforms")
    platform_experience: dict[str, str] | str | None = Field(default=None, description="Platform skill level(s)")
    brand_assets: BrandAssets = Field(default_factory=BrandAssets)

    # --- Section 6: Challenges ---
    challenges: list[str] = Field(default_factory=list)
    additional_challenges: str | None = Field(default=None)

    # --- Section 7: Strengths & Opportunities ---
    strengths: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    additional_notes: str | None = Field(default=None)

    # --- Section 8: Market Situation ---
    seasonality: list[SeasonalityEntry] = Field(default_factory=list)
    seasonality_other: str | None = Field(default=None)
    competitor_behavior: str | None = Field(default=None)
    stock_availability: str | None = Field(default=None)
    recent_price_changes: bool | None = Field(default=None)
    price_change_details: str | None = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "business_type": "Restaurant/Food",
                    "industry": "Italian Restaurant",
                    "business_size": "small-team",
                    "business_stage": "growing",
                    "location": {"city": "Colombo", "district": "Colombo 07"},
                    "products_services": "Authentic Italian pizzas, pastas, and desserts",
                    "unique_selling_proposition": "Only wood-fired Neapolitan pizza in Colombo",
                    "monthly_budget": "LKR 50,000 - 100,000/month",
                    "has_marketing_team": False,
                    "content_creation_capacity": ["Professional photography", "Social media management"],
                    "primary_goal": "brand-awareness",
                    "secondary_goals": ["Build community engagement", "Promote offers"],
                    "demographics": {
                        "age_range": "25-34",
                        "gender": ["All genders"],
                        "income_level": "Upper middle",
                    },
                    "target_location": "Colombo Metropolitan Area",
                    "interests": ["Food & Dining", "Entertainment"],
                    "buying_frequency": "weekly",
                    "preferred_platforms": ["Instagram", "Facebook", "TikTok"],
                    "platform_experience": {
                        "Instagram": "intermediate",
                        "Facebook": "beginner",
                        "TikTok": "none",
                    },
                    "brand_assets": {
                        "has_logo": True,
                        "has_brand_style": False,
                        "brand_colors": ["#FF5733", "#2C3E50"],
                    },
                    "challenges": ["content-creation", "inconsistent-posting"],
                    "strengths": ["high-quality-products", "unique-location"],
                    "opportunities": ["social-media-growth", "local-community-events"],
                    "seasonality": [
                        {"category": "Holiday & Lifestyle", "subcategories": ["Valentine's Day", "Christmas"]}
                    ],
                    "competitor_behavior": "Competitors run heavy discounts on weekends",
                    "stock_availability": "always-available",
                    "recent_price_changes": False,
                }
            ]
        }
    }
