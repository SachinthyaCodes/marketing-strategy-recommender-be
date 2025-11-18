"""
LLM Utilities
Utilities for interacting with Language Learning Models (OpenAI GPT, etc.)
"""

import openai
import os
from typing import Dict, Any, List, Optional, Union
import logging
from dotenv import load_dotenv
import asyncio
import json

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for interacting with Language Learning Models
    """
    
    def __init__(self):
        """Initialize the LLM client with configuration"""
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Configure OpenAI client
        openai.api_key = self.api_key
        
        # Default model configuration
        self.default_model = "gpt-3.5-turbo"
        self.default_max_tokens = 1000
        self.default_temperature = 0.7
        
        # Rate limiting configuration
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_message: Optional[str] = None,
        json_format: bool = False
    ) -> str:
        """
        Generate a completion using the specified LLM
        
        Args:
            prompt: The prompt to send to the model
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            system_message: Optional system message
            json_format: Whether to request JSON format output
            
        Returns:
            Generated text completion
        """
        
        model = model or self.default_model
        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature or self.default_temperature
        
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        elif json_format:
            messages.append({
                "role": "system",
                "content": "You are a helpful assistant that responds with valid JSON format."
            })
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.max_retries):
            try:
                response = await self._call_openai_api(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    json_format=json_format
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.warning(f"LLM API call failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt == self.max_retries - 1:
                    raise Exception(f"LLM API call failed after {self.max_retries} attempts: {str(e)}")
                
                # Wait before retrying
                await asyncio.sleep(self.retry_delay * (attempt + 1))
    
    async def generate_structured_response(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured response that follows a specific schema
        
        Args:
            prompt: The prompt to send to the model
            schema: JSON schema for the expected response structure
            model: Model to use
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON response matching the schema
        """
        
        # Create a prompt that includes schema information
        schema_prompt = f"""
        {prompt}
        
        Please respond with a valid JSON object that follows this schema:
        {json.dumps(schema, indent=2)}
        
        Ensure your response is valid JSON and includes all required fields.
        """
        
        response_text = await self.generate_completion(
            prompt=schema_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for structured output
            json_format=True
        )
        
        try:
            # Parse JSON response
            response_data = json.loads(response_text)
            
            # Basic validation against schema (simplified)
            self._validate_response_schema(response_data, schema)
            
            return response_data
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}")
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate a chat completion with conversation context
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response text
        """
        
        model = model or self.default_model
        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature or self.default_temperature
        
        for attempt in range(self.max_retries):
            try:
                response = await self._call_openai_api(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.warning(f"Chat completion failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt == self.max_retries - 1:
                    raise Exception(f"Chat completion failed after {self.max_retries} attempts: {str(e)}")
                
                await asyncio.sleep(self.retry_delay * (attempt + 1))
    
    async def generate_embeddings(
        self,
        text: str,
        model: str = "text-embedding-ada-002"
    ) -> List[float]:
        """
        Generate embeddings for the given text
        
        Args:
            text: Text to generate embeddings for
            model: Embedding model to use
            
        Returns:
            List of embedding values
        """
        
        try:
            response = await openai.Embedding.acreate(
                model=model,
                input=text
            )
            
            return response['data'][0]['embedding']
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise Exception(f"Embedding generation failed: {str(e)}")
    
    async def _call_openai_api(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        json_format: bool = False
    ):
        """Make API call to OpenAI"""
        
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Add response format for JSON if requested
        if json_format and "gpt-3.5-turbo" in model or "gpt-4" in model:
            kwargs["response_format"] = {"type": "json_object"}
        
        # Use the synchronous client but wrap in async
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai.ChatCompletion.create(**kwargs)
        )
        
        return response
    
    def _validate_response_schema(self, response: Dict[str, Any], schema: Dict[str, Any]):
        """Basic schema validation (simplified)"""
        
        if "required" in schema:
            for required_field in schema["required"]:
                if required_field not in response:
                    raise ValueError(f"Required field '{required_field}' missing from response")
        
        if "properties" in schema:
            for field_name, field_schema in schema["properties"].items():
                if field_name in response:
                    field_value = response[field_name]
                    expected_type = field_schema.get("type")
                    
                    if expected_type == "string" and not isinstance(field_value, str):
                        raise ValueError(f"Field '{field_name}' should be string, got {type(field_value)}")
                    elif expected_type == "number" and not isinstance(field_value, (int, float)):
                        raise ValueError(f"Field '{field_name}' should be number, got {type(field_value)}")
                    elif expected_type == "array" and not isinstance(field_value, list):
                        raise ValueError(f"Field '{field_name}' should be array, got {type(field_value)}")
                    elif expected_type == "object" and not isinstance(field_value, dict):
                        raise ValueError(f"Field '{field_name}' should be object, got {type(field_value)}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        
        # Simple estimation: ~4 characters per token on average
        return len(text) // 4
    
    def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit
        
        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens allowed
            
        Returns:
            Truncated text
        """
        
        estimated_tokens = self.estimate_tokens(text)
        
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

class LLMPromptBuilder:
    """
    Utility class for building structured prompts
    """
    
    @staticmethod
    def build_profile_analysis_prompt(customer_data: Dict[str, Any]) -> str:
        """Build a prompt for customer profile analysis"""
        
        return f"""
        Analyze the following customer data and provide comprehensive insights:
        
        Customer Data:
        {json.dumps(customer_data, indent=2)}
        
        Please provide:
        1. Demographic analysis
        2. Behavioral patterns
        3. Psychographic insights
        4. Customer segment classification
        5. Marketing recommendations
        6. Engagement strategies
        
        Be specific and actionable in your analysis.
        """
    
    @staticmethod
    def build_strategy_generation_prompt(
        profile: Dict[str, Any],
        objectives: List[str],
        budget: str,
        timeline: str
    ) -> str:
        """Build a prompt for marketing strategy generation"""
        
        return f"""
        Create a comprehensive marketing strategy based on:
        
        Customer Profile:
        {json.dumps(profile, indent=2)}
        
        Campaign Requirements:
        - Objectives: {', '.join(objectives)}
        - Budget: {budget}
        - Timeline: {timeline}
        
        Please provide a detailed strategy including:
        1. Strategic overview and positioning
        2. Target audience insights
        3. Channel recommendations
        4. Content strategy
        5. Campaign tactics
        6. Budget allocation
        7. Success metrics
        8. Implementation timeline
        
        Make recommendations specific and actionable.
        """
    
    @staticmethod
    def build_content_generation_prompt(
        topic: str,
        audience: str,
        tone: str,
        format_type: str
    ) -> str:
        """Build a prompt for content generation"""
        
        return f"""
        Create {format_type} content about "{topic}" for {audience}.
        
        Requirements:
        - Tone: {tone}
        - Format: {format_type}
        - Target Audience: {audience}
        
        The content should be:
        1. Engaging and relevant to the audience
        2. Aligned with the specified tone
        3. Appropriate for the format
        4. Actionable and valuable
        5. Optimized for the target channel
        
        Include suggestions for:
        - Headlines/titles
        - Key messaging
        - Call-to-action
        - Visual elements (if applicable)
        """

# Utility functions
def get_llm_client() -> LLMClient:
    """Get a configured LLM client instance"""
    return LLMClient()

def safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON from text, returning None if invalid"""
    try:
        # Try to find JSON within the text
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    
    return None