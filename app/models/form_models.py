"""
Pydantic models for form data validation
Based on the frontend form structure
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BusinessSize(str, Enum):
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"

class BusinessStage(str, Enum):
    STARTUP = "startup"
    GROWING = "growing"
    ESTABLISHED = "established"

class MarketingGoal(str, Enum):
    INCREASE_BRAND_AWARENESS = "increase_brand_awareness"
    GENERATE_LEADS = "generate_leads"
    BOOST_SALES = "boost_sales"
    CUSTOMER_RETENTION = "customer_retention"
    MARKET_EXPANSION = "market_expansion"
    IMPROVE_CUSTOMER_ENGAGEMENT = "improve_customer_engagement"

class SocialPlatform(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    WHATSAPP = "whatsapp"

class Challenge(str, Enum):
    LIMITED_BUDGET = "limited_budget"
    LACK_OF_EXPERTISE = "lack_of_expertise"
    TIME_CONSTRAINTS = "time_constraints"
    MEASURING_ROI = "measuring_roi"
    CONTENT_CREATION = "content_creation"
    REACHING_TARGET_AUDIENCE = "reaching_target_audience"

# Form Step Models
class BusinessProfile(BaseModel):
    """Step 1: Business Profile"""
    business_name: str = Field(..., min_length=1, max_length=200)
    business_type: str = Field(..., min_length=1, max_length=100)
    business_size: BusinessSize
    business_stage: BusinessStage
    location: str = Field(..., min_length=1, max_length=100)
    years_in_business: Optional[int] = Field(None, ge=0, le=100)
    unique_selling_proposition: str = Field(..., min_length=1, max_length=500)

class BudgetResources(BaseModel):
    """Step 2: Budget & Resources"""
    monthly_marketing_budget: Optional[float] = Field(None, ge=0)
    budget_currency: str = Field(default="LKR", max_length=10)
    team_size: Optional[int] = Field(None, ge=1, le=1000)
    has_marketing_experience: Optional[bool] = None
    external_support_budget: Optional[float] = Field(None, ge=0)

class BusinessGoals(BaseModel):
    """Step 3: Business Goals"""
    primary_marketing_goal: MarketingGoal
    secondary_marketing_goals: List[MarketingGoal] = Field(default_factory=list)
    specific_objectives: Optional[str] = Field(None, max_length=1000)
    success_metrics: Optional[str] = Field(None, max_length=500)

class TargetAudience(BaseModel):
    """Step 4: Target Audience"""
    age_range: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=50)
    location_demographics: Optional[str] = Field(None, max_length=200)
    interests: Optional[str] = Field(None, max_length=500)
    buying_behavior: Optional[str] = Field(None, max_length=500)
    pain_points: Optional[str] = Field(None, max_length=500)

class PlatformsPreferences(BaseModel):
    """Step 5: Platforms & Preferences"""
    preferred_platforms: List[SocialPlatform] = Field(default_factory=list)
    current_online_presence: Optional[str] = Field(None, max_length=500)
    website_url: Optional[str] = Field(None, max_length=200)
    has_brand_assets: Optional[bool] = None
    brand_guidelines: Optional[str] = Field(None, max_length=500)

class CurrentChallenges(BaseModel):
    """Step 6: Current Challenges"""
    main_challenges: List[Challenge] = Field(default_factory=list)
    specific_obstacles: Optional[str] = Field(None, max_length=1000)
    previous_marketing_efforts: Optional[str] = Field(None, max_length=500)
    what_didnt_work: Optional[str] = Field(None, max_length=500)

class StrengthsOpportunities(BaseModel):
    """Step 7: Strengths & Opportunities"""
    business_strengths: Optional[str] = Field(None, max_length=500)
    competitive_advantages: Optional[str] = Field(None, max_length=500)
    market_opportunities: Optional[str] = Field(None, max_length=500)
    growth_areas: Optional[str] = Field(None, max_length=500)

class MarketSituation(BaseModel):
    """Step 8: Market Situation"""
    seasonal_factors: Optional[str] = Field(None, max_length=500)
    competition_level: Optional[str] = Field(None, max_length=100)
    market_trends: Optional[str] = Field(None, max_length=500)
    pricing_strategy: Optional[str] = Field(None, max_length=300)

# Complete Form Model
class MarketingFormData(BaseModel):
    """Complete marketing strategy form data"""
    business_profile: BusinessProfile
    budget_resources: BudgetResources
    business_goals: BusinessGoals
    target_audience: TargetAudience
    platforms_preferences: PlatformsPreferences
    current_challenges: CurrentChallenges
    strengths_opportunities: StrengthsOpportunities
    market_situation: MarketSituation
    
    # Metadata
    form_language: Optional[str] = Field(None, max_length=10)
    submission_source: Optional[str] = Field(None, max_length=100)
    user_agent: Optional[str] = Field(None, max_length=500)

# Database Storage Model
class FormSubmission(BaseModel):
    """Model for database storage"""
    id: Optional[str] = None
    form_data: MarketingFormData
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = Field(default="submitted", max_length=50)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Response Models
class SubmissionResponse(BaseModel):
    """Response model for form submission"""
    id: str
    message: str
    status: str
    created_at: datetime

class SubmissionWithStrategyResponse(BaseModel):
    """Response model for form submission with generated strategy"""
    id: str
    message: str
    status: str
    created_at: datetime
    strategy: Optional[Dict[str, Any]] = None
    strategy_error: Optional[str] = None

class SubmissionListResponse(BaseModel):
    """Response model for listing submissions"""
    submissions: List[FormSubmission]
    total: int
    page: int
    limit: int