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
    SubmissionListResponse
)
from app.services.database import DatabaseService
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency to get database service
def get_db_service() -> DatabaseService:
    settings = get_settings()
    return DatabaseService(settings)

@router.post("/forms/submit", response_model=SubmissionResponse)
async def submit_form(
    form_data: MarketingFormData,
    request: Request,
    db_service: DatabaseService = Depends(get_db_service)
):
    """Submit marketing strategy form data"""
    try:
        # Extract request metadata
        metadata = {
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
            "submission_source": "web_form"
        }
        
        # Create submission in database
        submission = await db_service.create_submission(form_data, metadata)
        
        return SubmissionResponse(
            id=submission.id,
            message="Form submitted successfully",
            status="submitted",
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