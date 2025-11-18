"""
Profile API endpoints
Handles customer profile creation, retrieval, and marketing strategy generation
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from app.utils.validators import (
    ProfileCreateRequest,
    ProfileResponse,
    StrategyRequest,
    StrategyResponse
)
from app.agents.profile_builder import ProfileBuilderAgent
from app.tools.profile_extraction import ProfileExtractor

router = APIRouter()

# In-memory storage for demo purposes
# In production, use a proper database
profiles_db: Dict[str, Dict[str, Any]] = {}

@router.post("/profile/build", response_model=ProfileResponse)
async def build_profile(request: ProfileCreateRequest):
    """
    Build a customer profile from provided data
    """
    try:
        # Generate unique profile ID
        profile_id = str(uuid.uuid4())
        
        # Extract profile information
        extractor = ProfileExtractor()
        extracted_data = await extractor.extract_profile_data(request.dict())
        
        # Use profile builder agent to enhance the profile
        builder = ProfileBuilderAgent()
        enhanced_profile = await builder.build_profile(extracted_data)
        
        # Store profile
        profile = {
            "id": profile_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "raw_data": request.dict(),
            "extracted_data": extracted_data,
            "enhanced_profile": enhanced_profile,
            "status": "completed"
        }
        
        profiles_db[profile_id] = profile
        
        return ProfileResponse(
            id=profile_id,
            status="completed",
            profile_data=enhanced_profile,
            created_at=profile["created_at"],
            updated_at=profile["updated_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build profile: {str(e)}"
        )

@router.get("/profile/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str):
    """
    Retrieve an existing customer profile
    """
    if profile_id not in profiles_db:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    
    profile = profiles_db[profile_id]
    
    return ProfileResponse(
        id=profile_id,
        status=profile["status"],
        profile_data=profile["enhanced_profile"],
        created_at=profile["created_at"],
        updated_at=profile["updated_at"]
    )

@router.post("/profile/{profile_id}/strategy", response_model=StrategyResponse)
async def generate_strategy(profile_id: str, request: StrategyRequest):
    """
    Generate marketing strategy for a specific profile
    """
    if profile_id not in profiles_db:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    
    try:
        profile = profiles_db[profile_id]
        
        # Use profile builder agent to generate strategy
        builder = ProfileBuilderAgent()
        strategy = await builder.generate_marketing_strategy(
            profile["enhanced_profile"],
            request.campaign_objectives,
            request.budget_range,
            request.timeline
        )
        
        return StrategyResponse(
            profile_id=profile_id,
            strategy=strategy,
            generated_at=datetime.utcnow().isoformat(),
            campaign_objectives=request.campaign_objectives,
            budget_range=request.budget_range,
            timeline=request.timeline
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate strategy: {str(e)}"
        )

@router.get("/profiles")
async def list_profiles(skip: int = 0, limit: int = 10):
    """
    List all customer profiles with pagination
    """
    profile_list = list(profiles_db.values())[skip:skip + limit]
    
    return {
        "profiles": [
            {
                "id": profile["id"],
                "status": profile["status"],
                "created_at": profile["created_at"],
                "updated_at": profile["updated_at"]
            }
            for profile in profile_list
        ],
        "total": len(profiles_db),
        "skip": skip,
        "limit": limit
    }

@router.delete("/profile/{profile_id}")
async def delete_profile(profile_id: str):
    """
    Delete a customer profile
    """
    if profile_id not in profiles_db:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    
    del profiles_db[profile_id]
    
    return {"message": "Profile deleted successfully"}