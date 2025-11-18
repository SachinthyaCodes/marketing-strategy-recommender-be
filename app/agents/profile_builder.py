"""
Profile Builder Agent
AI agent responsible for building comprehensive customer profiles and generating marketing strategies
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from app.utils.llm import LLMClient
from app.utils.validators import CustomerProfile, MarketingStrategy

class ProfileBuilderAgent:
    """
    AI agent that builds detailed customer profiles and generates marketing strategies
    """
    
    def __init__(self):
        self.llm_client = LLMClient()
        
    async def build_profile(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a comprehensive customer profile from extracted data
        
        Args:
            extracted_data: Raw extracted profile data
            
        Returns:
            Enhanced customer profile with insights and segments
        """
        
        profile_prompt = self._create_profile_prompt(extracted_data)
        
        try:
            response = await self.llm_client.generate_completion(
                prompt=profile_prompt,
                max_tokens=1500,
                temperature=0.3
            )
            
            # Parse the response and structure it
            profile_data = self._parse_profile_response(response, extracted_data)
            
            return profile_data
            
        except Exception as e:
            raise Exception(f"Failed to build profile: {str(e)}")
    
    async def generate_marketing_strategy(
        self,
        profile_data: Dict[str, Any],
        campaign_objectives: List[str],
        budget_range: str,
        timeline: str
    ) -> Dict[str, Any]:
        """
        Generate a marketing strategy based on customer profile
        
        Args:
            profile_data: Customer profile data
            campaign_objectives: List of campaign objectives
            budget_range: Budget range for the campaign
            timeline: Campaign timeline
            
        Returns:
            Comprehensive marketing strategy
        """
        
        strategy_prompt = self._create_strategy_prompt(
            profile_data, campaign_objectives, budget_range, timeline
        )
        
        try:
            response = await self.llm_client.generate_completion(
                prompt=strategy_prompt,
                max_tokens=2000,
                temperature=0.4
            )
            
            strategy_data = self._parse_strategy_response(
                response, campaign_objectives, budget_range, timeline
            )
            
            return strategy_data
            
        except Exception as e:
            raise Exception(f"Failed to generate strategy: {str(e)}")
    
    def _create_profile_prompt(self, extracted_data: Dict[str, Any]) -> str:
        """Create prompt for profile building"""
        
        return f"""
        You are an expert marketing analyst. Based on the following customer data, create a comprehensive customer profile with insights and recommendations.

        Customer Data:
        {json.dumps(extracted_data, indent=2)}

        Please provide a detailed analysis including:

        1. Customer Demographics & Psychographics
        2. Behavioral Patterns
        3. Pain Points & Motivations
        4. Preferred Communication Channels
        5. Customer Segment Classification
        6. Value Proposition Alignment
        7. Engagement Preferences
        8. Purchase Behavior Insights

        Format your response as a structured JSON object with the following sections:
        - demographics
        - psychographics
        - behavioral_patterns
        - pain_points
        - motivations
        - communication_preferences
        - customer_segment
        - value_propositions
        - engagement_score
        - purchase_likelihood
        - recommended_touchpoints

        Provide actionable insights and be specific about marketing implications.
        """
    
    def _create_strategy_prompt(
        self,
        profile_data: Dict[str, Any],
        objectives: List[str],
        budget: str,
        timeline: str
    ) -> str:
        """Create prompt for strategy generation"""
        
        return f"""
        You are a strategic marketing consultant. Based on the customer profile and campaign requirements, create a comprehensive marketing strategy.

        Customer Profile:
        {json.dumps(profile_data, indent=2)}

        Campaign Requirements:
        - Objectives: {', '.join(objectives)}
        - Budget Range: {budget}
        - Timeline: {timeline}

        Please provide a detailed marketing strategy including:

        1. Strategic Overview & Positioning
        2. Target Audience Segmentation
        3. Channel Strategy & Mix
        4. Content Strategy & Messaging
        5. Campaign Tactics & Executions
        6. Budget Allocation & Timeline
        7. KPIs & Success Metrics
        8. Risk Assessment & Mitigation

        Format your response as a structured JSON object with:
        - strategy_overview
        - positioning_statement
        - channel_mix
        - content_strategy
        - campaign_tactics
        - budget_allocation
        - timeline_milestones
        - success_metrics
        - expected_outcomes
        - risk_factors
        - recommendations

        Be specific and actionable in your recommendations.
        """
    
    def _parse_profile_response(
        self, response: str, original_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse and structure the profile response"""
        
        try:
            # Try to extract JSON from the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed_data = json.loads(json_str)
            else:
                # Fallback: create structured data from text
                parsed_data = self._extract_profile_from_text(response)
            
            # Ensure required fields are present
            profile = {
                "demographics": parsed_data.get("demographics", {}),
                "psychographics": parsed_data.get("psychographics", {}),
                "behavioral_patterns": parsed_data.get("behavioral_patterns", []),
                "pain_points": parsed_data.get("pain_points", []),
                "motivations": parsed_data.get("motivations", []),
                "communication_preferences": parsed_data.get("communication_preferences", []),
                "customer_segment": parsed_data.get("customer_segment", "General"),
                "value_propositions": parsed_data.get("value_propositions", []),
                "engagement_score": parsed_data.get("engagement_score", 7.0),
                "purchase_likelihood": parsed_data.get("purchase_likelihood", "Medium"),
                "recommended_touchpoints": parsed_data.get("recommended_touchpoints", []),
                "original_data": original_data,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            return profile
            
        except Exception as e:
            # Fallback profile structure
            return {
                "demographics": original_data.get("demographics", {}),
                "psychographics": {},
                "behavioral_patterns": [],
                "pain_points": ["Analysis temporarily unavailable"],
                "motivations": ["To be determined"],
                "communication_preferences": ["email", "social_media"],
                "customer_segment": "General",
                "value_propositions": [],
                "engagement_score": 7.0,
                "purchase_likelihood": "Medium",
                "recommended_touchpoints": ["email", "content_marketing"],
                "original_data": original_data,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "error": f"Parsing error: {str(e)}"
            }
    
    def _parse_strategy_response(
        self,
        response: str,
        objectives: List[str],
        budget: str,
        timeline: str
    ) -> Dict[str, Any]:
        """Parse and structure the strategy response"""
        
        try:
            # Try to extract JSON from the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed_data = json.loads(json_str)
            else:
                # Fallback: create structured data from text
                parsed_data = self._extract_strategy_from_text(response)
            
            strategy = {
                "strategy_overview": parsed_data.get("strategy_overview", "Comprehensive marketing approach"),
                "positioning_statement": parsed_data.get("positioning_statement", ""),
                "channel_mix": parsed_data.get("channel_mix", []),
                "content_strategy": parsed_data.get("content_strategy", {}),
                "campaign_tactics": parsed_data.get("campaign_tactics", []),
                "budget_allocation": parsed_data.get("budget_allocation", {}),
                "timeline_milestones": parsed_data.get("timeline_milestones", []),
                "success_metrics": parsed_data.get("success_metrics", []),
                "expected_outcomes": parsed_data.get("expected_outcomes", []),
                "risk_factors": parsed_data.get("risk_factors", []),
                "recommendations": parsed_data.get("recommendations", []),
                "campaign_objectives": objectives,
                "budget_range": budget,
                "timeline": timeline,
                "generated_timestamp": datetime.utcnow().isoformat()
            }
            
            return strategy
            
        except Exception as e:
            # Fallback strategy structure
            return {
                "strategy_overview": "Comprehensive digital marketing strategy",
                "positioning_statement": "Customer-focused approach with data-driven insights",
                "channel_mix": ["email_marketing", "social_media", "content_marketing"],
                "content_strategy": {"approach": "Educational and engaging content"},
                "campaign_tactics": ["Awareness campaigns", "Lead generation", "Retention programs"],
                "budget_allocation": {"digital": "70%", "traditional": "30%"},
                "timeline_milestones": ["Week 1-2: Setup", "Week 3-8: Execution", "Week 9-12: Optimization"],
                "success_metrics": ["Conversion rate", "Cost per acquisition", "Customer lifetime value"],
                "expected_outcomes": ["Increased brand awareness", "Higher conversion rates", "Improved customer retention"],
                "risk_factors": ["Market competition", "Budget constraints", "Timeline pressures"],
                "recommendations": ["Focus on digital channels", "Monitor KPIs closely", "Be ready to adapt"],
                "campaign_objectives": objectives,
                "budget_range": budget,
                "timeline": timeline,
                "generated_timestamp": datetime.utcnow().isoformat(),
                "error": f"Parsing error: {str(e)}"
            }
    
    def _extract_profile_from_text(self, text: str) -> Dict[str, Any]:
        """Extract profile data from unstructured text"""
        # Basic text parsing fallback
        return {
            "demographics": {},
            "psychographics": {},
            "behavioral_patterns": [],
            "pain_points": [],
            "motivations": [],
            "communication_preferences": ["email"],
            "customer_segment": "General",
            "value_propositions": [],
            "engagement_score": 7.0,
            "purchase_likelihood": "Medium",
            "recommended_touchpoints": ["email"]
        }
    
    def _extract_strategy_from_text(self, text: str) -> Dict[str, Any]:
        """Extract strategy data from unstructured text"""
        # Basic text parsing fallback
        return {
            "strategy_overview": "Multi-channel marketing approach",
            "positioning_statement": "",
            "channel_mix": ["email", "social_media"],
            "content_strategy": {},
            "campaign_tactics": [],
            "budget_allocation": {},
            "timeline_milestones": [],
            "success_metrics": [],
            "expected_outcomes": [],
            "risk_factors": [],
            "recommendations": []
        }