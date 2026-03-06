import json
import logging
import re
from dataclasses import dataclass, field

from app.ai_core.advanced_confidence_model import (
    AdvancedConfidenceModel,
    ConfidenceBreakdown,
)
from app.ai_core.groq_client import generate_strategy
from app.ai_core.rag_engine import RAGEngine, RetrievalResult
from app.models.sme_profile import SMEProfile
from app.models.strategy_model import MarketingStrategy

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a professional AI marketing strategist specializing in "
    "Sri Lankan SME markets. You produce structured, data-driven marketing "
    "strategies grounded in retrieved knowledge and local market context. "
    "Your reasoning MUST: (1) cite specific retrieved knowledge to justify each "
    "recommendation, (2) explain WHY each platform was chosen for THIS specific "
    "business and audience, (3) provide concrete actionable next steps, "
    "(4) address how the budget split maximizes ROI given the stated goals, "
    "and (5) identify risks or limitations of the strategy."
)


@dataclass(frozen=True)
class GenerationResult:
    """Full output from the strategy generation pipeline.

    Carries the validated strategy alongside retrieval and scoring
    metadata needed by the service layer for drift detection and storage.
    """

    strategy: MarketingStrategy
    retrieval_result: RetrievalResult
    query_context: str
    retrieved_text_combined: str
    confidence_breakdown: ConfidenceBreakdown


class StrategyGenerator:
    """End-to-end strategy generation pipeline with RAG and advanced confidence.

    Orchestrates:
        1. Semantic query construction from the SME profile.
        2. Context retrieval via RAG (with similarity scores + dates).
        3. Structured prompt assembly.
        4. LLM invocation via Groq.
        5. Safe JSON parsing and Pydantic validation.
        6. Advanced multi-factor confidence scoring (Phase 5).
    """

    def __init__(self, top_k: int = 5) -> None:
        self._rag_engine = RAGEngine()
        self._confidence_model = AdvancedConfidenceModel()
        self._top_k = top_k

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, sme_profile: SMEProfile) -> GenerationResult:
        """Generate a validated marketing strategy for the given SME profile.

        Args:
            sme_profile: Comprehensive SME business profile.

        Returns:
            GenerationResult containing the strategy and pipeline metadata.

        Raises:
            ValueError: If LLM output cannot be parsed or validated.
            RuntimeError: If the LLM call itself fails.
        """
        # Step 1 — Query context
        query = self._build_query_context(sme_profile)
        logger.info("Retrieval query: %s", query[:120])

        # Step 2 — RAG retrieval
        retrieval = self._retrieve_context(query)
        logger.info(
            "Retrieved %d documents (scores: %s).",
            len(retrieval.documents),
            [round(s, 3) for s in retrieval.similarity_scores],
        )

        # Step 3 — Prompt assembly & LLM call
        user_prompt = self._build_prompt(sme_profile, retrieval.documents)
        raw_response = generate_strategy(user_prompt, system_prompt=SYSTEM_PROMPT)
        logger.debug("LLM raw response: %s", raw_response[:500])

        # Step 4 — Parse LLM output
        strategy = self._parse_response(raw_response)

        # Step 5 — Advanced multi-factor confidence scoring (Phase 5)
        #   Components computed from measurable signals — NO LLM involved.
        trend_recency = self._confidence_model.calculate_trend_recency(
            document_created_dates=retrieval.created_dates,
        )
        similarity = self._confidence_model.calculate_similarity(
            similarity_values=retrieval.similarity_scores,
        )
        data_coverage = self._confidence_model.calculate_data_coverage(
            retrieved_docs_count=len(retrieval.documents),
            top_k=self._top_k,
        )
        platform_stability = self._confidence_model.calculate_platform_stability(
            recommended_platforms=strategy.recommended_platforms,
        )

        breakdown = self._confidence_model.compute_confidence(
            trend_recency_score=trend_recency,
            similarity_score=similarity,
            data_coverage_score=data_coverage,
            platform_stability_score=platform_stability,
        )

        # Attach scores to the strategy model
        strategy.confidence_score = breakdown.final_confidence
        strategy.trend_recency_score = breakdown.trend_recency_score
        strategy.similarity_score = breakdown.similarity_score
        strategy.data_coverage_score = breakdown.data_coverage_score
        strategy.platform_stability_score = breakdown.platform_stability_score
        logger.info("Advanced confidence: %.3f", breakdown.final_confidence)

        # Step 6 — Combine context text for drift analysis
        combined_context = query + " " + " ".join(retrieval.documents)

        return GenerationResult(
            strategy=strategy,
            retrieval_result=retrieval,
            query_context=query,
            retrieved_text_combined=combined_context,
            confidence_breakdown=breakdown,
        )

    # ------------------------------------------------------------------
    # Step 1 — Query context generation
    # ------------------------------------------------------------------

    def _build_query_context(self, profile: SMEProfile) -> str:
        """Convert the SME profile into a semantic retrieval query.

        Captures industry, location, audience, budget, and goals so that
        the vector search finds the most relevant knowledge entries.
        """
        industry = profile.industry or profile.business_type
        location = f"{profile.location.city}"
        if profile.location.district:
            location = f"{profile.location.district}, {location}"

        goals = profile.primary_goal
        if profile.secondary_goals:
            goals += ", " + ", ".join(profile.secondary_goals[:3])

        return (
            f"Marketing strategy for a {industry} business "
            f"located in {location} "
            f"targeting {profile.demographics.age_range} age group, "
            f"{profile.demographics.income_level} income, "
            f"with a monthly budget of {profile.monthly_budget}. "
            f"Goals: {goals}. "
            f"Preferred platforms: {', '.join(profile.preferred_platforms)}"
        )

    # ------------------------------------------------------------------
    # Step 2 — RAG retrieval
    # ------------------------------------------------------------------

    def _retrieve_context(self, query: str) -> RetrievalResult:
        """Retrieve relevant knowledge documents, falling back gracefully."""
        try:
            return self._rag_engine.retrieve_context(query, top_k=self._top_k)
        except RuntimeError:
            logger.warning("RAG retrieval failed — proceeding without context.")
            return RetrievalResult(documents=[], similarity_scores=[])

    # ------------------------------------------------------------------
    # Step 3 — Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt(
        self, profile: SMEProfile, retrieved_docs: list[str]
    ) -> str:
        """Assemble the full user-role prompt for the LLM."""
        profile_block = self._format_profile(profile)
        context_block = self._format_retrieved_context(retrieved_docs)

        return f"""SME PROFILE:
{profile_block}

RETRIEVED KNOWLEDGE:
{context_block}

INSTRUCTIONS:
- Generate a structured marketing strategy in STRICT JSON format.
- Use retrieved knowledge to justify decisions where applicable — cite specific articles or data points.
- Align recommendations with the SME's budget, goals, and local market conditions.
- In the "reasoning" field, provide a DETAILED explanation that:
  (a) Explains why each recommended platform suits this specific business and audience.
  (b) Justifies the budget allocation percentages with concrete logic.
  (c) References specific retrieved knowledge articles that support the decisions.
  (d) Identifies 1-2 potential risks and how the strategy mitigates them.
  (e) Suggests 2-3 concrete first-week action items the business owner should take.
- Provide a confidence_score between 0 and 1.
- DO NOT include any text outside the JSON object.

Return EXACTLY this JSON structure:
{{
    "strategy_summary": "<high-level strategy overview>",
    "recommended_platforms": ["<platform1>", "<platform2>"],
    "content_strategy": "<content creation and distribution plan>",
    "budget_allocation": {{"<platform_name>": <percentage_number>}},
    "reasoning": "<rationale referencing context and profile>",
    "confidence_score": <float between 0 and 1>
}}"""

    def _format_profile(self, p: SMEProfile) -> str:
        """Render the SME profile as a human-readable text block."""
        industry = p.industry or p.business_type
        location = p.location.city
        if p.location.district:
            location = f"{p.location.district}, {location}"

        goals = [p.primary_goal] + (p.secondary_goals or [])

        lines = [
            f"- Business Type: {p.business_type}",
            f"- Industry: {industry}",
            f"- Business Size: {p.business_size}",
            f"- Business Stage: {p.business_stage}",
            f"- Location: {location}",
            f"- Products/Services: {p.products_services}",
            f"- USP: {p.unique_selling_proposition}",
            f"- Monthly Budget: {p.monthly_budget}",
            f"- Has Marketing Team: {'Yes' if p.has_marketing_team else 'No'}",
            f"- Content Creation Capacity: {', '.join(p.content_creation_capacity) or 'None'}",
            f"- Marketing Goals: {', '.join(goals)}",
            f"- Target Age Range: {p.demographics.age_range}",
            f"- Target Gender: {', '.join(p.demographics.gender)}",
            f"- Target Income Level: {p.demographics.income_level}",
            f"- Target Location: {p.target_location}",
            f"- Target Interests: {', '.join(p.interests) or 'N/A'}",
            f"- Buying Frequency: {p.buying_frequency}",
            f"- Preferred Platforms: {', '.join(p.preferred_platforms)}",
            f"- Challenges: {', '.join(p.challenges) or 'None specified'}",
            f"- Strengths: {', '.join(p.strengths) or 'None specified'}",
            f"- Opportunities: {', '.join(p.opportunities) or 'None specified'}",
        ]

        if p.competitor_behavior:
            lines.append(f"- Competitor Behavior: {p.competitor_behavior}")
        if p.stock_availability:
            lines.append(f"- Stock Availability: {p.stock_availability}")
        if p.seasonality:
            seasons = "; ".join(
                f"{s.category}: {', '.join(s.subcategories)}" for s in p.seasonality
            )
            lines.append(f"- Seasonality Factors: {seasons}")
        if p.additional_notes:
            lines.append(f"- Additional Notes: {p.additional_notes}")

        return "\n".join(lines)

    @staticmethod
    def _format_retrieved_context(documents: list[str]) -> str:
        """Format retrieved documents into a numbered reference list."""
        if not documents:
            return "No relevant knowledge available."
        return "\n".join(
            f"{i}. {doc}" for i, doc in enumerate(documents, start=1)
        )

    # ------------------------------------------------------------------
    # Step 4 — Response parsing & validation
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(raw_response: str) -> MarketingStrategy:
        """Extract, parse, and validate JSON from the LLM response.

        Handles common LLM quirks:
            - Markdown code fences (```json ... ```)
            - Leading/trailing text around the JSON object

        Args:
            raw_response: Raw text from the LLM.

        Returns:
            Validated MarketingStrategy.

        Raises:
            ValueError: If JSON extraction, parsing, or validation fails.
        """
        json_str = StrategyGenerator._extract_json(raw_response)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            logger.error("JSON parse error: %s | raw: %s", exc, raw_response[:300])
            raise ValueError(f"Invalid JSON from LLM: {exc}") from exc

        try:
            strategy = MarketingStrategy.model_validate(data)
        except Exception as exc:
            logger.error("Pydantic validation failed: %s", exc)
            raise ValueError(f"Strategy validation failed: {exc}") from exc

        return strategy

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract the first JSON object from potentially noisy LLM output."""
        cleaned = text.strip()

        # Strip markdown code fences
        fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
        match = fence_pattern.search(cleaned)
        if match:
            return match.group(1).strip()

        # Try to find a raw JSON object
        brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if brace_match:
            return brace_match.group(0).strip()

        return cleaned
