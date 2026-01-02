"""
Strategy Generator Client Service
Handles communication with the Strategy Generator API (port 8002)
"""

import httpx
import logging
from typing import Dict, Any, Optional
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class StrategyGeneratorClient:
    """
    HTTP client for Strategy Generator service
    Sends form data and receives generated marketing strategies
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize strategy generator client
        
        Args:
            settings: Application settings with strategy_generator_url
        """
        self.base_url = settings.strategy_generator_url
        self.timeout = httpx.Timeout(120.0)  # 2 minutes for LLM generation
        self.client = httpx.AsyncClient(timeout=self.timeout)
        logger.info(f"Strategy Generator Client initialized: {self.base_url}")
    
    async def generate_strategy(
        self,
        submission_id: str,
        sme_profile: Dict[str, Any],
        trend_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate marketing strategy from SME profile
        
        Args:
            submission_id: Form submission ID
            sme_profile: Complete business profile from form
            trend_data: Optional pre-fetched trend data (will fetch if None)
        
        Returns:
            Strategy generation response with success status and strategy data
        
        Raises:
            Exception: If strategy generation fails
        """
        try:
            logger.info(f"Generating strategy for submission: {submission_id}")
            
            # Prepare request payload
            payload = {
                "sme_profile": sme_profile,
                "trend_data": trend_data or {"signals": []}  # Empty if not provided
            }
            
            # Call strategy generator API
            response = await self.client.post(
                f"{self.base_url}/strategy/generate",
                json=payload,
                timeout=self.timeout
            )
            
            # Check response status
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Strategy generation failed: {response.status_code} - {error_detail}")
                raise Exception(f"Strategy API returned {response.status_code}: {error_detail}")
            
            result = response.json()
            
            # Check success flag
            if not result.get("success", False):
                error = result.get("error", "Unknown error")
                logger.error(f"Strategy generation unsuccessful: {error}")
                raise Exception(f"Strategy generation failed: {error}")
            
            logger.info(f"Strategy generated successfully for submission {submission_id}")
            return result
        
        except httpx.TimeoutException:
            logger.error(f"Strategy generation timeout for submission {submission_id}")
            raise Exception("Strategy generation timed out (120s)")
        
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Strategy Generator at {self.base_url}")
            raise Exception(
                f"Strategy Generator service unavailable. "
                f"Ensure it's running on {self.base_url}"
            )
        
        except Exception as e:
            logger.error(f"Strategy generation error: {str(e)}", exc_info=True)
            raise
    
    async def generate_strategy_from_submission(
        self,
        submission_id: str,
        backend_url: str,
        trend_agent_url: str,
        relevance_threshold: float = 60.0
    ) -> Dict[str, Any]:
        """
        Generate strategy using submission ID (fetches data internally)
        
        This method lets the strategy generator fetch data itself.
        Useful when backend doesn't want to manage data fetching.
        
        Args:
            submission_id: Form submission ID
            backend_url: Backend API URL for fetching submission
            trend_agent_url: Trend Agent API URL
            relevance_threshold: Minimum trend relevance score
        
        Returns:
            Strategy generation response
        """
        try:
            logger.info(f"Requesting strategy from submission ID: {submission_id}")
            
            payload = {
                "submission_id": submission_id,
                "backend_url": backend_url,
                "trend_agent_url": trend_agent_url,
                "relevance_threshold": relevance_threshold
            }
            
            response = await self.client.post(
                f"{self.base_url}/strategy/from-submission",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Strategy generation failed: {response.status_code}")
                raise Exception(f"Strategy API returned {response.status_code}: {error_detail}")
            
            result = response.json()
            
            if not result.get("success", False):
                error = result.get("error", "Unknown error")
                raise Exception(f"Strategy generation failed: {error}")
            
            return result
        
        except Exception as e:
            logger.error(f"Strategy generation from submission failed: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Strategy Generator service is healthy
        
        Returns:
            Health status dict with service info
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=httpx.Timeout(5.0)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
        
        except Exception as e:
            logger.warning(f"Strategy Generator health check failed: {str(e)}")
            return {
                "status": "unavailable",
                "error": str(e)
            }
    
    async def close(self):
        """Close HTTP client connection"""
        await self.client.aclose()
        logger.debug("Strategy Generator client closed")
