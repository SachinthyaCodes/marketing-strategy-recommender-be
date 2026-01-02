"""
API routes for form submission endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import List, Optional
import logging
from datetime import datetime

from app.models.form_models import (
    MarketingFormData, 
    FormSubmission, 
    SubmissionResponse, 
    SubmissionListResponse,
    SubmissionWithStrategyResponse
)
from app.models.user_models import TokenData
from app.services.auth import get_current_user
from app.services.database import DatabaseService
from app.services.strategy_client import StrategyGeneratorClient
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency to get database service
def get_db_service() -> DatabaseService:
    settings = get_settings()
    return DatabaseService(settings)

# Dependency to get strategy client
async def get_strategy_client():
    settings = get_settings()
    client = StrategyGeneratorClient(settings)
    try:
        yield client
    finally:
        await client.close()

@router.post("/forms/save-profile", response_model=SubmissionResponse)
async def save_business_profile(
    form_data: MarketingFormData,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """
    Save business profile (form data) without generating strategy
    
    Args:
        form_data: Complete marketing form data (8 steps)
        current_user: Authenticated user from JWT token
    
    Returns:
        Submission response with saved profile ID
    """
    try:
        # Extract request metadata
        metadata = {
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
            "submission_source": "web_form",
            "user_id": current_user.user_id,
            "user_email": current_user.email
        }
        
        # Save submission in database with user_id
        submission = await db_service.create_submission(form_data, metadata, user_id=current_user.user_id)
        logger.info(f"Business profile saved: {submission.id} for user {current_user.email}")
        
        return SubmissionResponse(
            id=submission.id,
            message="Business profile saved successfully",
            status="pending",
            created_at=submission.created_at
        )
        
    except Exception as e:
        logger.error(f"Error submitting form: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit form: {str(e)}"
        )

@router.get("/forms/submissions", response_model=SubmissionListResponse)
async def list_submissions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db_service: DatabaseService = Depends(get_db_service)
):
    """List form submissions with pagination"""
    try:
        offset = (page - 1) * limit
        
        # Get submissions
        submissions = await db_service.list_submissions(
            limit=limit,
            offset=offset,
            status=status
        )
        
        # Get total count
        total = await db_service.get_submissions_count(status=status)
        
        return SubmissionListResponse(
            submissions=submissions,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing submissions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve submissions: {str(e)}"
        )

@router.get("/forms/submissions/{submission_id}", response_model=FormSubmission)
async def get_submission(
    submission_id: str,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get a specific form submission by ID"""
    try:
        submission = await db_service.get_submission(submission_id)
        
        if not submission:
            raise HTTPException(
                status_code=404,
                detail=f"Submission with ID {submission_id} not found"
            )
        
        return submission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving submission {submission_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve submission: {str(e)}"
        )

@router.put("/forms/submissions/{submission_id}/status")
async def update_submission_status(
    submission_id: str,
    status: str,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Update submission status"""
    try:
        success = await db_service.update_submission_status(submission_id, status)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Submission with ID {submission_id} not found"
            )
        
        return {
            "message": f"Submission {submission_id} status updated to {status}",
            "submission_id": submission_id,
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating submission {submission_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update submission: {str(e)}"
        )

@router.delete("/forms/submissions/{submission_id}")
async def delete_submission(
    submission_id: str,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Delete a form submission"""
    try:
        success = await db_service.delete_submission(submission_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Submission with ID {submission_id} not found"
            )
        
        return {
            "message": f"Submission {submission_id} deleted successfully",
            "submission_id": submission_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting submission {submission_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete submission: {str(e)}"
        )

@router.get("/forms/stats")
async def get_form_stats(
    db_service: DatabaseService = Depends(get_db_service)
):
    """Get form submission statistics"""
    try:
        total_submissions = await db_service.get_submissions_count()
        submitted_count = await db_service.get_submissions_count(status="submitted")
        processed_count = await db_service.get_submissions_count(status="processed")
        
        return {
            "total_submissions": total_submissions,
            "submitted": submitted_count,
            "processed": processed_count,
            "pending": total_submissions - processed_count
        }
        
    except Exception as e:
        logger.error(f"Error getting form stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.post("/forms/submissions/{submission_id}/generate-strategy")
async def generate_strategy_for_submission(
    submission_id: str,
    db_service: DatabaseService = Depends(get_db_service),
    strategy_client: StrategyGeneratorClient = Depends(get_strategy_client)
):
    """
    Manually trigger strategy generation for an existing submission
    
    Useful for:
    - Regenerating strategies with updated trends
    - Generating strategies for old submissions
    - Testing strategy generation
    """
    try:
        # Fetch submission
        submission = await db_service.get_submission(submission_id)
        
        if not submission:
            raise HTTPException(
                status_code=404,
                detail=f"Submission {submission_id} not found"
            )
        
        # Convert form data to SME profile
        sme_profile = _convert_form_to_sme_profile(submission.form_data)
        
        # Generate strategy
        strategy_result = await strategy_client.generate_strategy(
            submission_id=submission_id,
            sme_profile=sme_profile,
            trend_data=None
        )
        
        if not strategy_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Strategy generation failed: {strategy_result.get('error')}"
            )
        
        # Update submission with strategy
        strategy_data = strategy_result.get("strategy")
        await db_service.update_submission_strategy(submission_id, strategy_data)
        
        return {
            "message": "Strategy generated successfully",
            "submission_id": submission_id,
            "strategy": strategy_data,
            "metadata": strategy_result.get("metadata", {})
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating strategy: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate strategy: {str(e)}"
        )


@router.get("/health/services")
async def check_services_health(
    strategy_client: StrategyGeneratorClient = Depends(get_strategy_client)
):
    """
    Check health of all connected services
    
    Returns status of:
    - Backend (this service)
    - Strategy Generator
    """
    try:
        # Check strategy generator
        strategy_health = await strategy_client.health_check()
        
        return {
            "backend": {
                "status": "healthy",
                "service": "marketing-strategy-recommender-be"
            },
            "strategy_generator": strategy_health
        }
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "backend": {
                "status": "healthy",
                "service": "marketing-strategy-recommender-be"
            },
            "strategy_generator": {
                "status": "error",
                "error": str(e)
            }
        }


# Helper function to convert form data to SME profile
def _convert_form_to_sme_profile(form_data: MarketingFormData) -> dict:
    """
    Convert backend form model to strategy generator's expected format
    
    Handles camelCase/snake_case conversion and flattening
    """
    profile = form_data.business_profile
    budget = form_data.budget_resources
    goals = form_data.business_goals
    audience = form_data.target_audience
    platforms = form_data.platforms_preferences
    challenges = form_data.current_challenges
    strengths = form_data.strengths_opportunities
    market = form_data.market_situation
    
    return {
        "business_name": profile.business_name,
        "industry": profile.business_type,
        "business_size": profile.business_size.value,
        "business_stage": profile.business_stage.value,
        "location": profile.location,
        "years_in_business": profile.years_in_business or 0,
        "unique_selling_proposition": profile.unique_selling_proposition,
        
        "monthly_budget": budget.monthly_marketing_budget or 0,
        "budget_currency": budget.budget_currency,
        "team_size": budget.team_size or 1,
        "has_marketing_experience": budget.has_marketing_experience or False,
        
        "goals": [
            goals.primary_marketing_goal.value
        ] + [g.value for g in goals.secondary_marketing_goals],
        "specific_objectives": goals.specific_objectives,
        "success_metrics": goals.success_metrics,
        
        "target_audience": {
            "age_range": audience.age_range,
            "gender": audience.gender,
            "location": audience.location_demographics,
            "interests": audience.interests,
            "buying_behavior": audience.buying_behavior,
            "pain_points": audience.pain_points
        },
        
        "platform_preferences": [p.value for p in platforms.preferred_platforms],
        "current_online_presence": platforms.current_online_presence,
        "website_url": platforms.website_url,
        "has_brand_assets": platforms.has_brand_assets,
        
        "challenges": [c.value for c in challenges.main_challenges],
        "specific_obstacles": challenges.specific_obstacles,
        "previous_marketing_efforts": challenges.previous_marketing_efforts,
        
        "business_strengths": strengths.business_strengths,
        "competitive_advantages": strengths.competitive_advantages,
        "market_opportunities": strengths.market_opportunities,
        
        "seasonal_factors": market.seasonal_factors,
        "competition_level": market.competition_level,
        "market_trends": market.market_trends,
        "pricing_strategy": market.pricing_strategy
    }