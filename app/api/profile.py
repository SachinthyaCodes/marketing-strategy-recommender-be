# app/api/profile.py
"""
Profile API Endpoints

API endpoints for building and managing business profiles using the Profile Builder Agent.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import time
import logging

from app.agents.profile_builder import ProfileBuilderAgent
from app.utils.validators import ProfileCreateRequest, ProfileResponse, BusinessProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])

# In-memory storage for demo (replace with database in production)
profiles_storage: Dict[str, Dict[str, Any]] = {}

class RawInput(BaseModel):
    """Legacy model for backward compatibility"""
    text: str = Field(..., description="Raw business input text")

class EnhancedProfileRequest(BaseModel):
    """Enhanced profile creation request"""
    raw_input: str = Field(..., description="Raw business description from SME")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Additional user context")
    processing_preferences: Optional[Dict[str, Any]] = Field(None, description="Processing preferences")
    
    class Config:
        schema_extra = {
            "example": {
                "raw_input": "I have a small bakery in Galle. We make fresh cakes and pastries. Looking to get more customers through social media. Budget is around 25k per month. Main challenge is we don't have time to create content.",
                "user_context": {
                    "business_name": "Sweet Dreams Bakery",
                    "contact_email": "owner@sweetdreams.lk"
                },
                "processing_preferences": {
                    "include_assumptions": True,
                    "suggest_platforms": True
                }
            }
        }

@router.post("/build", response_model=ProfileResponse, summary="Build Business Profile")
async def build_business_profile(request: EnhancedProfileRequest) -> ProfileResponse:
    """
    Build a comprehensive business profile from raw SME input.
    
    This endpoint uses the Profile Builder Agent to:
    - Clean and understand messy input (including Sinhala + English)
    - Extract structured business information
    - Fill gaps with intelligent assumptions
    - Generate standardized business profile
    
    Perfect for SMEs who want to describe their business in any format.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Building profile from input: {request.raw_input[:100]}...")
        
        # Initialize Profile Builder Agent
        agent = ProfileBuilderAgent(temperature=0.1)
        
        # Build the profile
        profile_data = await agent.build_profile(
            raw_input=request.raw_input,
            user_context=request.user_context
        )
        
        # Create BusinessProfile instance
        business_profile = BusinessProfile(**profile_data)
        
        # Store profile (in production, save to database)
        profile_id = f"profile_{int(time.time())}_{hash(request.raw_input) % 10000}"
        profiles_storage[profile_id] = {
            "profile": profile_data,
            "raw_input": request.raw_input,
            "created_at": time.time()
        }
        
        processing_time = (time.time() - start_time) * 1000
        
        logger.info(f"Successfully built profile for {business_profile.business_identity.business_type} business")
        
        return ProfileResponse(
            success=True,
            profile=business_profile,
            summary=business_profile.get_summary(),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Profile building failed: {str(e)}")
        
        return ProfileResponse(
            success=False,
            error_message=f"Failed to build profile: {str(e)}",
            processing_time_ms=processing_time
        )

@router.post("/", response_model=dict, summary="Build Profile (Legacy)")
async def create_profile_legacy(payload: RawInput) -> dict:
    """
    Legacy endpoint for backward compatibility.
    Builds profile using the original interface.
    """
    try:
        # Use the enhanced endpoint internally
        request = EnhancedProfileRequest(raw_input=payload.text)
        response = await build_business_profile(request)
        
        if response.success and response.profile:
            return response.profile.dict()
        else:
            raise HTTPException(status_code=500, detail=response.error_message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", summary="List All Profiles")
async def list_profiles():
    """
    List all created profiles (for development/testing).
    """
    profiles_list = []
    for profile_id, data in profiles_storage.items():
        profile = BusinessProfile(**data["profile"])
        profiles_list.append({
            "id": profile_id,
            "business_type": profile.business_identity.business_type,
            "location": profile.business_identity.location,
            "created_at": data["created_at"],
            "summary": profile.get_summary()
        })
    
    return {
        "profiles": profiles_list,
        "total_count": len(profiles_list)
    }

@router.get("/{profile_id}", response_model=ProfileResponse, summary="Get Profile by ID")
async def get_profile(profile_id: str) -> ProfileResponse:
    """
    Retrieve a specific profile by ID.
    """
    if profile_id not in profiles_storage:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    try:
        profile_data = profiles_storage[profile_id]["profile"]
        business_profile = BusinessProfile(**profile_data)
        
        return ProfileResponse(
            success=True,
            profile=business_profile,
            summary=business_profile.get_summary()
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            error_message=f"Failed to retrieve profile: {str(e)}"
        )

@router.delete("/{profile_id}", summary="Delete Profile")
async def delete_profile(profile_id: str):
    """
    Delete a specific profile.
    """
    if profile_id not in profiles_storage:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    del profiles_storage[profile_id]
    
    return {
        "message": f"Profile {profile_id} deleted successfully"
    }

@router.post("/analyze", summary="Analyze Input Without Building")
async def analyze_input(request: RawInput):
    """
    Analyze raw input without building full profile.
    Useful for quick insights or validation.
    """
    try:
        from app.tools.profile_extraction import ProfileExtractor
        
        extractor = ProfileExtractor()
        
        # Extract insights
        insights = {
            "detected_business_type": extractor.extract_business_type(request.text),
            "detected_location": extractor.extract_location(request.text),
            "detected_platforms": extractor.extract_platforms(request.text),
            "detected_budget": extractor.extract_budget(request.text),
            "detected_challenges": extractor.extract_challenges(request.text),
            "detected_strengths": extractor.extract_strengths(request.text),
            "normalized_input": extractor.normalize_sinhala_terms(request.text)
        }
        
        return {
            "success": True,
            "insights": insights,
            "input_length": len(request.text),
            "has_sinhala_terms": any(term in request.text.lower() for term in 
                ['kade', 'restaurant eka', 'salon eka', 'awareness ekak', 'photos nane'])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
