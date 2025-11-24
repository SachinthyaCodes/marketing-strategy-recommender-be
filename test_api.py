"""
Test script to verify the form submission API
"""
import requests
import json
from datetime import datetime

# Test data - sample marketing form submission
test_form_data = {
    "business_profile": {
        "business_name": "Test Sri Lankan Business",
        "business_type": "Restaurant",
        "business_size": "small",
        "business_stage": "growing",
        "location": "Colombo",
        "years_in_business": 3,
        "unique_selling_proposition": "Authentic Sri Lankan cuisine with modern twist"
    },
    "budget_resources": {
        "monthly_marketing_budget": 50000,
        "budget_currency": "LKR",
        "team_size": 5,
        "has_marketing_experience": False,
        "external_support_budget": 20000
    },
    "business_goals": {
        "primary_marketing_goal": "increase_brand_awareness",
        "secondary_marketing_goals": ["generate_leads", "boost_sales"],
        "specific_objectives": "Increase local customer base by 30%",
        "success_metrics": "Monthly revenue growth, customer count"
    },
    "target_audience": {
        "age_range": "25-45",
        "gender": "All",
        "location_demographics": "Colombo and suburbs",
        "interests": "Food, dining out, Sri Lankan culture",
        "buying_behavior": "Weekend dining, special occasions",
        "pain_points": "Finding authentic but modern Sri Lankan food"
    },
    "platforms_preferences": {
        "preferred_platforms": ["facebook", "instagram", "whatsapp"],
        "current_online_presence": "Basic Facebook page",
        "website_url": "https://example-restaurant.lk",
        "has_brand_assets": True,
        "brand_guidelines": "Traditional colors with modern design"
    },
    "current_challenges": {
        "main_challenges": ["limited_budget", "lack_of_expertise", "content_creation"],
        "specific_obstacles": "Don't know how to create engaging social media content",
        "previous_marketing_efforts": "Word of mouth, local newspaper ads",
        "what_didnt_work": "Newspaper ads didn't bring many customers"
    },
    "strengths_opportunities": {
        "business_strengths": "Excellent food quality, loyal local customers",
        "competitive_advantages": "Family recipes, authentic ingredients",
        "market_opportunities": "Growing food delivery market",
        "growth_areas": "Online ordering, catering services"
    },
    "market_situation": {
        "seasonal_factors": "Higher demand during festivals and holidays",
        "competition_level": "High local competition",
        "market_trends": "Increased demand for authentic Sri Lankan food",
        "pricing_strategy": "Competitive pricing with value focus"
    },
    "form_language": "en",
    "submission_source": "test_script"
}

def test_api():
    """Test the form submission API"""
    base_url = "http://localhost:8000"
    
    try:
        # Test root endpoint
        print("Testing root endpoint...")
        response = requests.get(f"{base_url}/")
        print(f"Root response: {response.json()}")
        
        # Test health endpoint
        print("\nTesting health endpoint...")
        response = requests.get(f"{base_url}/health")
        print(f"Health response: {response.json()}")
        
        # Test form submission
        print("\nTesting form submission...")
        response = requests.post(
            f"{base_url}/api/v1/forms/submit",
            json=test_form_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Form submitted successfully!")
            print(f"Submission ID: {result['id']}")
            print(f"Status: {result['status']}")
            print(f"Created at: {result['created_at']}")
            
            # Test retrieving the submission
            submission_id = result['id']
            print(f"\nTesting retrieval of submission {submission_id}...")
            response = requests.get(f"{base_url}/api/v1/forms/submissions/{submission_id}")
            
            if response.status_code == 200:
                submission = response.json()
                print(f"✅ Retrieved submission successfully!")
                print(f"Business name: {submission['form_data']['business_profile']['business_name']}")
                print(f"Form language: {submission['form_data']['form_language']}")
            else:
                print(f"❌ Failed to retrieve submission: {response.text}")
                
        else:
            print(f"❌ Form submission failed: {response.status_code}")
            print(f"Error: {response.text}")
            
        # Test listing submissions
        print("\nTesting submissions list...")
        response = requests.get(f"{base_url}/api/v1/forms/submissions")
        
        if response.status_code == 200:
            submissions_list = response.json()
            print(f"✅ Retrieved submissions list!")
            print(f"Total submissions: {submissions_list['total']}")
            print(f"Current page: {submissions_list['page']}")
            print(f"Submissions on page: {len(submissions_list['submissions'])}")
        else:
            print(f"❌ Failed to retrieve submissions list: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    print("🚀 Testing Marketing Strategy Recommender API")
    print("=" * 50)
    test_api()
    print("\n" + "=" * 50)
    print("✨ API testing complete!")