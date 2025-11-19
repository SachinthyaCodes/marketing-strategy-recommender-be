# app/utils/llm.py
"""
LLM Utilities

Provides Ollama integration for the Profile Builder Agent.
Supports local open-source models via Ollama API.
"""

import os
import asyncio
import logging
import requests
import json
from typing import Any, Optional, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
MODEL_TYPE = os.getenv("MODEL_TYPE", "ollama")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1:8b-instruct-q4_0")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))

class OllamaClient:
    """
    Client for interacting with Ollama API
    """
    
    def __init__(
        self, 
        base_url: str = OLLAMA_BASE_URL,
        model_name: str = MODEL_NAME,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
        timeout: int = LLM_TIMEOUT
    ):
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response using Ollama chat API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system message
            
        Returns:
            Generated text response
        """
        try:
            messages = []
            
            # Add system message if provided
            if system_prompt:
                messages.append({
                    "role": "system", 
                    "content": system_prompt
                })
            
            # Add user prompt
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                }
            }
            
            # Make async request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                )
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["message"]["content"].strip()
            
        except requests.exceptions.ConnectionError:
            raise Exception(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Please ensure Ollama is running with: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise Exception(
                f"Ollama request timed out after {self.timeout} seconds. "
                "Try reducing input length or increasing timeout."
            )
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"LLM generation failed: {str(e)}")
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check if Ollama is running and model is available
        
        Returns:
            Health status information
        """
        try:
            # Check if Ollama is running
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": "Ollama server not responding",
                    "ollama_running": False,
                    "model_available": False
                }
            
            # Check if our model is available
            models_data = response.json()
            models = models_data.get("models", [])
            
            model_available = any(
                self.model_name in model.get("name", "")
                for model in models
            )
            
            return {
                "status": "healthy" if model_available else "warning",
                "message": "Model available" if model_available else f"Model {self.model_name} not found",
                "ollama_running": True,
                "model_available": model_available,
                "available_models": [model.get("name") for model in models]
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "Cannot connect to Ollama server",
                "ollama_running": False,
                "model_available": False,
                "suggestion": "Run 'ollama serve' to start Ollama"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "ollama_running": False,
                "model_available": False
            }

# Global client instance
_ollama_client: Optional[OllamaClient] = None

def get_llm_client() -> OllamaClient:
    """
    Get global Ollama client instance
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client

def validate_llm_configuration() -> dict:
    """
    Validate current LLM configuration and return status
    """
    client = get_llm_client()
    health_status = client.check_health()
    
    config_status = {
        "model_type": MODEL_TYPE,
        "model_name": MODEL_NAME,
        "base_url": OLLAMA_BASE_URL,
        "is_valid": health_status["status"] == "healthy",
        "error": None if health_status["status"] == "healthy" else health_status["message"],
        "recommendations": []
    }
    
    if not health_status["ollama_running"]:
        config_status["recommendations"].append("Start Ollama with: ollama serve")
    
    if health_status["ollama_running"] and not health_status["model_available"]:
        config_status["recommendations"].append(
            f"Download model with: ollama pull {MODEL_NAME}"
        )
    
    return config_status

def get_model_info() -> dict:
    """
    Get information about the current model configuration
    """
    client = get_llm_client()
    health_status = client.check_health()
    
    return {
        "model_type": MODEL_TYPE,
        "model_name": MODEL_NAME,
        "base_url": OLLAMA_BASE_URL,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "timeout": LLM_TIMEOUT,
        "configuration_valid": health_status["status"] == "healthy",
        "available_models": health_status.get("available_models", [])
    }

# Utility functions
def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    # Simple estimation: ~4 characters per token on average
    return len(text) // 4

def truncate_to_token_limit(text: str, max_tokens: int) -> str:
    """
    Truncate text to fit within token limit
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens allowed
        
    Returns:
        Truncated text
    """
    estimated_tokens = estimate_tokens(text)
    
    if estimated_tokens <= max_tokens:
        return text
    
    # Calculate approximate character limit
    char_limit = max_tokens * 4
    truncated = text[:char_limit]
    
    # Try to truncate at word boundary
    last_space = truncated.rfind(' ')
    if last_space > char_limit * 0.9:  # Only if we don't lose too much
        truncated = truncated[:last_space]
    
    return truncated + "..."

def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling various formats
    
    Args:
        response: Raw LLM response text
        
    Returns:
        Parsed JSON data
    """
    try:
        # Try direct parsing first
        return json.loads(response.strip())
    except json.JSONDecodeError:
        try:
            # Try extracting JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try finding JSON-like content
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
                
            raise ValueError("No valid JSON found in response")
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
