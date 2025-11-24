"""
Supabase database service for form data storage
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
from supabase import create_client, Client
from postgrest.exceptions import APIError

from app.config.settings import Settings
from app.models.form_models import MarketingFormData, FormSubmission

logger = logging.getLogger(__name__)

class DatabaseService:
    """Supabase database service"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        self.table_name = "marketing_form_submissions"
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            # Test connection by querying the table
            result = self.client.table(self.table_name).select("count", count="exact").limit(1).execute()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def create_submission(self, form_data: MarketingFormData, metadata: Optional[Dict[str, Any]] = None) -> FormSubmission:
        """Create a new form submission"""
        try:
            # Prepare data for insertion
            submission_data = {
                "form_data": form_data.dict(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": "submitted"
            }
            
            # Add metadata if provided
            if metadata:
                submission_data.update(metadata)
            
            # Insert into database
            result = self.client.table(self.table_name).insert(submission_data).execute()
            
            if result.data and len(result.data) > 0:
                submission_record = result.data[0]
                logger.info(f"Form submission created with ID: {submission_record.get('id')}")
                
                return FormSubmission(
                    id=submission_record.get("id"),
                    form_data=form_data,
                    created_at=datetime.fromisoformat(submission_record.get("created_at").replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(submission_record.get("updated_at").replace("Z", "+00:00")),
                    status=submission_record.get("status", "submitted")
                )
            else:
                raise Exception("No data returned from insert operation")
                
        except APIError as e:
            logger.error(f"Database API error: {e}")
            raise Exception(f"Failed to create submission: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating submission: {e}")
            raise
    
    async def get_submission(self, submission_id: str) -> Optional[FormSubmission]:
        """Get a specific form submission by ID"""
        try:
            result = self.client.table(self.table_name).select("*").eq("id", submission_id).execute()
            
            if result.data and len(result.data) > 0:
                record = result.data[0]
                return FormSubmission(
                    id=record.get("id"),
                    form_data=MarketingFormData(**record.get("form_data", {})),
                    created_at=datetime.fromisoformat(record.get("created_at").replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(record.get("updated_at").replace("Z", "+00:00")),
                    status=record.get("status", "submitted")
                )
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving submission {submission_id}: {e}")
            raise
    
    async def list_submissions(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[FormSubmission]:
        """List form submissions with pagination"""
        try:
            query = self.client.table(self.table_name).select("*")
            
            if status:
                query = query.eq("status", status)
            
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            result = query.execute()
            
            submissions = []
            if result.data:
                for record in result.data:
                    try:
                        submission = FormSubmission(
                            id=record.get("id"),
                            form_data=MarketingFormData(**record.get("form_data", {})),
                            created_at=datetime.fromisoformat(record.get("created_at").replace("Z", "+00:00")),
                            updated_at=datetime.fromisoformat(record.get("updated_at").replace("Z", "+00:00")),
                            status=record.get("status", "submitted")
                        )
                        submissions.append(submission)
                    except Exception as e:
                        logger.error(f"Error parsing submission record {record.get('id')}: {e}")
                        continue
            
            return submissions
            
        except Exception as e:
            logger.error(f"Error listing submissions: {e}")
            raise
    
    async def update_submission_status(self, submission_id: str, status: str) -> bool:
        """Update submission status"""
        try:
            result = self.client.table(self.table_name).update({
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", submission_id).execute()
            
            return bool(result.data and len(result.data) > 0)
            
        except Exception as e:
            logger.error(f"Error updating submission {submission_id}: {e}")
            raise
    
    async def delete_submission(self, submission_id: str) -> bool:
        """Delete a form submission"""
        try:
            result = self.client.table(self.table_name).delete().eq("id", submission_id).execute()
            return bool(result.data and len(result.data) > 0)
            
        except Exception as e:
            logger.error(f"Error deleting submission {submission_id}: {e}")
            raise
    
    async def get_submissions_count(self, status: Optional[str] = None) -> int:
        """Get total count of submissions"""
        try:
            query = self.client.table(self.table_name).select("count", count="exact")
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            return result.count or 0
            
        except Exception as e:
            logger.error(f"Error getting submissions count: {e}")
            return 0