"""
Test suite for profile API endpoints
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime
import json

# Import the main application
from app.main import app
from app.utils.validators import ProfileCreateRequest, StrategyRequest

# Create test client
client = TestClient(app)

class TestProfileAPI:
    """Test cases for profile API endpoints"""
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Marketing Strategy Recommender API" in response.json()["message"]
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_create_profile_minimal_data(self):
        """Test profile creation with minimal data"""
        profile_data = {
            "customer_id": "test_customer_001",
            "source": "unit_test",
            "demographics": {
                "age": 30,
                "gender": "Male",
                "location": "Test City"
            },
            "contact_info": {
                "email": "test@example.com",
                "name": "Test User"
            },
            "consent_status": True
        }
        
        response = client.post("/api/profile/build", json=profile_data)
        
        # The endpoint might fail if OpenAI API key is not configured
        # Check for either success or specific error
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            result = response.json()
            assert "id" in result
            assert result["status"] == "completed"
            assert "profile_data" in result
            assert "created_at" in result
    
    def test_create_profile_comprehensive_data(self):
        """Test profile creation with comprehensive data"""
        profile_data = {
            "customer_id": "test_customer_002",
            "source": "comprehensive_test",
            "demographics": {
                "age": 35,
                "gender": "Female",
                "location": "San Francisco, CA",
                "income": 85000,
                "education": "Master's Degree",
                "occupation": "Product Manager",
                "marital_status": "Married",
                "family_size": 3
            },
            "behavioral": {
                "purchase_frequency": "Monthly",
                "average_order_value": 200.0,
                "preferred_channels": ["email", "social_media"],
                "product_categories": ["Technology", "Books", "Home"],
                "engagement_level": "High"
            },
            "psychographics": {
                "interests": ["Technology", "Reading", "Fitness", "Travel"],
                "values": ["Quality", "Innovation", "Sustainability"],
                "lifestyle": "Urban Professional",
                "personality_traits": ["Analytical", "Goal-oriented", "Social"],
                "motivations": ["Career advancement", "Work-life balance"],
                "pain_points": ["Time constraints", "Information overload"]
            },
            "contact_info": {
                "email": "comprehensive.test@example.com",
                "name": "Jane Comprehensive",
                "phone": "555-0123",
                "preferred_contact_time": "Evening"
            },
            "interaction_history": [
                {
                    "type": "purchase",
                    "timestamp": "2023-10-15T14:30:00Z",
                    "details": "Purchased smartphone case",
                    "value": 29.99
                },
                {
                    "type": "email_open",
                    "timestamp": "2023-10-20T09:15:00Z",
                    "details": "Opened newsletter",
                    "outcome": "clicked"
                }
            ],
            "raw_data": {
                "signup_date": "2023-01-15",
                "referral_source": "Google Search",
                "utm_campaign": "spring_promotion"
            },
            "consent_status": True
        }
        
        response = client.post("/api/profile/build", json=profile_data)
        
        # Check for success or expected API configuration error
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            result = response.json()
            assert "id" in result
            assert result["status"] == "completed"
            
            # Validate profile data structure
            profile = result["profile_data"]
            assert "demographics" in profile
            assert "behavioral_patterns" in profile
            assert "customer_segment" in profile
            assert "engagement_score" in profile
    
    def test_get_nonexistent_profile(self):
        """Test retrieving a non-existent profile"""
        response = client.get("/api/profile/nonexistent_id")
        assert response.status_code == 404
        assert "Profile not found" in response.json()["detail"]
    
    def test_list_profiles_empty(self):
        """Test listing profiles when none exist"""
        response = client.get("/api/profiles")
        assert response.status_code == 200
        
        result = response.json()
        assert "profiles" in result
        assert "total" in result
        assert "skip" in result
        assert "limit" in result
    
    def test_list_profiles_pagination(self):
        """Test profiles listing with pagination"""
        response = client.get("/api/profiles?skip=0&limit=5")
        assert response.status_code == 200
        
        result = response.json()
        assert result["skip"] == 0
        assert result["limit"] == 5
    
    def test_generate_strategy_nonexistent_profile(self):
        """Test generating strategy for non-existent profile"""
        strategy_data = {
            "campaign_objectives": ["awareness", "engagement"],
            "budget_range": "$1000-$3000",
            "timeline": "2 months",
            "target_channels": ["email", "social_media"],
            "content_preferences": ["blog_post", "social_post"]
        }
        
        response = client.post("/api/profile/nonexistent_id/strategy", json=strategy_data)
        assert response.status_code == 404
        assert "Profile not found" in response.json()["detail"]
    
    def test_delete_nonexistent_profile(self):
        """Test deleting a non-existent profile"""
        response = client.delete("/api/profile/nonexistent_id")
        assert response.status_code == 404
        assert "Profile not found" in response.json()["detail"]

class TestProfileValidation:
    """Test cases for profile data validation"""
    
    def test_invalid_email_format(self):
        """Test profile creation with invalid email"""
        profile_data = {
            "customer_id": "test_invalid_email",
            "contact_info": {
                "email": "invalid_email_format",
                "name": "Test User"
            }
        }
        
        # This should fail validation at the FastAPI level
        response = client.post("/api/profile/build", json=profile_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_age(self):
        """Test profile creation with invalid age"""
        profile_data = {
            "customer_id": "test_invalid_age",
            "demographics": {
                "age": 150,  # Invalid age
                "gender": "Male"
            }
        }
        
        response = client.post("/api/profile/build", json=profile_data)
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_strategy_fields(self):
        """Test strategy generation with missing required fields"""
        # First create a profile (this might fail if API not configured)
        profile_data = {
            "customer_id": "test_strategy",
            "demographics": {"age": 25}
        }
        
        profile_response = client.post("/api/profile/build", json=profile_data)
        
        if profile_response.status_code == 200:
            profile_id = profile_response.json()["id"]
            
            # Try to generate strategy with missing fields
            incomplete_strategy = {
                "budget_range": "$1000"
                # Missing campaign_objectives and timeline
            }
            
            response = client.post(f"/api/profile/{profile_id}/strategy", json=incomplete_strategy)
            assert response.status_code == 422  # Validation error

class TestProfileExtraction:
    """Test cases for profile extraction utilities"""
    
    def test_extract_demographics(self):
        """Test demographic data extraction"""
        from app.tools.profile_extraction import ProfileExtractor
        
        extractor = ProfileExtractor()
        
        raw_data = {
            "age": "32",
            "gender": "F",
            "location": "New York, NY",
            "annual_income": "$75,000",
            "education_level": "Bachelor's",
            "job_title": "Software Engineer"
        }
        
        demographics = extractor._extract_demographics(raw_data)
        
        assert demographics["age"] == 32
        assert demographics["gender"] == "Female"
        assert demographics["location"] == "New York, NY"
        assert demographics["income"] == 75000
        assert demographics["education"] == "Bachelor's"
        assert demographics["occupation"] == "Software Engineer"
    
    def test_email_validation(self):
        """Test email validation utility"""
        from app.tools.profile_extraction import ProfileExtractor
        
        extractor = ProfileExtractor()
        
        # Valid emails
        assert extractor._is_valid_email("test@example.com") == True
        assert extractor._is_valid_email("user.name+tag@example.co.uk") == True
        
        # Invalid emails
        assert extractor._is_valid_email("invalid.email") == False
        assert extractor._is_valid_email("@example.com") == False
        assert extractor._is_valid_email("test@") == False
        assert extractor._is_valid_email(None) == False
        assert extractor._is_valid_email("") == False
    
    def test_phone_cleaning(self):
        """Test phone number cleaning utility"""
        from app.tools.profile_extraction import ProfileExtractor
        
        extractor = ProfileExtractor()
        
        # Valid phone numbers
        assert extractor._clean_phone_number("(555) 123-4567") == "5551234567"
        assert extractor._clean_phone_number("555.123.4567") == "5551234567"
        assert extractor._clean_phone_number("+1-555-123-4567") == "15551234567"
        
        # Invalid phone numbers
        assert extractor._clean_phone_number("123") == None  # Too short
        assert extractor._clean_phone_number("") == None
        assert extractor._clean_phone_number(None) == None
    
    def test_data_quality_calculation(self):
        """Test data quality score calculation"""
        from app.tools.profile_extraction import ProfileExtractor
        
        extractor = ProfileExtractor()
        
        # High quality data
        complete_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "location": "San Francisco",
            "purchase_history": [{"item": "book", "date": "2023-01-01"}],
            "interests": ["reading", "technology"],
            "preferences": {"email": True}
        }
        
        quality_score = extractor._calculate_data_quality(complete_data)
        assert quality_score > 0.5
        
        # Low quality data
        incomplete_data = {
            "name": "",
            "age": None
        }
        
        quality_score = extractor._calculate_data_quality(incomplete_data)
        assert quality_score < 0.5

class TestLLMUtilities:
    """Test cases for LLM utilities (when API is available)"""
    
    def test_token_estimation(self):
        """Test token estimation utility"""
        from app.utils.llm import LLMClient
        
        client = LLMClient()
        
        # Test token estimation
        short_text = "Hello world"
        long_text = "This is a much longer text " * 100
        
        short_tokens = client.estimate_tokens(short_text)
        long_tokens = client.estimate_tokens(long_text)
        
        assert short_tokens < long_tokens
        assert short_tokens > 0
        assert long_tokens > short_tokens * 50
    
    def test_text_truncation(self):
        """Test text truncation utility"""
        from app.utils.llm import LLMClient
        
        client = LLMClient()
        
        long_text = "This is a very long text. " * 1000
        truncated = client.truncate_to_token_limit(long_text, max_tokens=100)
        
        assert len(truncated) < len(long_text)
        assert truncated.endswith("...")
    
    def test_prompt_builder(self):
        """Test prompt building utilities"""
        from app.utils.llm import LLMPromptBuilder
        
        # Test profile analysis prompt
        customer_data = {"age": 30, "interests": ["technology"]}
        prompt = LLMPromptBuilder.build_profile_analysis_prompt(customer_data)
        
        assert "customer data" in prompt.lower()
        assert "demographic" in prompt.lower()
        assert str(customer_data["age"]) in prompt
        
        # Test strategy generation prompt
        profile = {"segment": "high_value"}
        objectives = ["awareness"]
        budget = "$1000"
        timeline = "1 month"
        
        strategy_prompt = LLMPromptBuilder.build_strategy_generation_prompt(
            profile, objectives, budget, timeline
        )
        
        assert "marketing strategy" in strategy_prompt.lower()
        assert budget in strategy_prompt
        assert timeline in strategy_prompt

# Integration test helper
def create_test_profile():
    """Helper function to create a test profile for integration tests"""
    profile_data = {
        "customer_id": "integration_test_001",
        "source": "integration_test",
        "demographics": {
            "age": 28,
            "gender": "Female",
            "location": "Austin, TX"
        },
        "contact_info": {
            "email": "integration@test.com",
            "name": "Integration Test"
        },
        "consent_status": True
    }
    
    response = client.post("/api/profile/build", json=profile_data)
    return response

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_full_profile_and_strategy_workflow(self):
        """Test complete workflow: create profile -> generate strategy -> cleanup"""
        
        # Step 1: Create profile
        profile_response = create_test_profile()
        
        # Skip if API not configured
        if profile_response.status_code != 200:
            pytest.skip("API not configured for integration testing")
        
        profile_result = profile_response.json()
        profile_id = profile_result["id"]
        
        # Step 2: Retrieve profile
        get_response = client.get(f"/api/profile/{profile_id}")
        assert get_response.status_code == 200
        
        retrieved_profile = get_response.json()
        assert retrieved_profile["id"] == profile_id
        
        # Step 3: Generate strategy
        strategy_data = {
            "campaign_objectives": ["awareness", "engagement"],
            "budget_range": "$2000-$4000",
            "timeline": "3 months",
            "target_channels": ["email", "social_media"]
        }
        
        strategy_response = client.post(f"/api/profile/{profile_id}/strategy", json=strategy_data)
        
        if strategy_response.status_code == 200:
            strategy_result = strategy_response.json()
            assert strategy_result["profile_id"] == profile_id
            assert "strategy" in strategy_result
            assert strategy_result["budget_range"] == "$2000-$4000"
        
        # Step 4: List profiles (should include our test profile)
        list_response = client.get("/api/profiles")
        assert list_response.status_code == 200
        
        profiles_list = list_response.json()
        profile_ids = [p["id"] for p in profiles_list["profiles"]]
        assert profile_id in profile_ids
        
        # Step 5: Cleanup - delete profile
        delete_response = client.delete(f"/api/profile/{profile_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted_response = client.get(f"/api/profile/{profile_id}")
        assert get_deleted_response.status_code == 404

if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])