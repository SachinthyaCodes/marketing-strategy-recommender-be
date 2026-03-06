# API Response Format Reference

## POST /api/v1/knowledge/add

### Success (200)
```json
{
  "status": "success",
  "data": {
    "id": "3f7a1c2d-5e8b-4a9f-b2c1-d3e4f5a6b7c8",
    "content": "Instagram algorithm prioritizes Reels...",
    "source_type": "algorithm_update",
    "platform": "instagram",
    "industry": "digital_marketing",
    "created_at": "2026-03-05T10:23:44.123456+00:00"
  }
}
```

### Error (422 - Validation)
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "content"],
      "msg": "Field required"
    }
  ]
}
```

### Error (503 - Database)
```json
{
  "detail": "Database connection failed: unable to reach Supabase"
}
```

---

## POST /api/v1/strategy/generate

### Success (200)
```json
{
  "strategy_summary": "Focus on community-driven organic growth with Instagram Reels showcasing sustainability, complemented by Facebook local awareness ads for weekday promotions. WhatsApp Business for loyalty and direct customer engagement.",
  
  "recommended_platforms": [
    "Instagram",
    "Facebook", 
    "WhatsApp Business"
  ],
  
  "content_strategy": "Create 3-4 weekly posts: (1) Behind-the-scenes Reels showing coffee roasting and eco-packaging, (2) Customer spotlight Stories for community building, (3) Weekday morning promotion graphics for Facebook ads, (4) Educational carousel posts about sustainability sourcing. Use Instagram location tags to attract nearby foot traffic.",
  
  "budget_allocation": {
    "Instagram Content Creation": 35.0,
    "Facebook Ads": 30.0,
    "WhatsApp Business Tools": 10.0,
    "Canva Pro Subscription": 15.0,
    "Micro-influencer Partnership": 10.0
  },
  
  "reasoning": "Based on retrieved knowledge showing Instagram Reels generate 67% higher engagement for F&B businesses (source: research doc), and Malaysian consumers aged 25-40 prefer sustainability messaging (market trend). Budget under RM2000 requires organic-first approach with targeted paid boosts. WhatsApp Business suits SME scale for personalized engagement.",
  
  "confidence_score": 0.817,
  "version": 1,
  "is_outdated": false,
  
  "trend_recency_score": 0.892,
  "similarity_score": 0.763,
  "data_coverage_score": 1.0,
  "platform_stability_score": 1.0,
  
  "drift_similarity": null,
  "drift_level": null,
  "regenerate_flag": null
}
```

### Field Explanations

| Field | Type | Description |
|---|---|---|
| `strategy_summary` | string | High-level overview of the complete strategy |
| `recommended_platforms` | array[string] | 2-4 platforms prioritized for this SME |
| `content_strategy` | string | Detailed content creation and distribution plan |
| `budget_allocation` | object | Platform/channel → percentage mapping (sums to ~100) |
| `reasoning` | string | Rationale citing retrieved knowledge and SME context |
| `confidence_score` | float (0-1) | **Final weighted confidence** |
| `version` | int | Strategy version (increments on HIGH drift) |
| `is_outdated` | bool | Whether drift detection flagged this as outdated |
| **Phase 5 Breakdown** | | |
| `trend_recency_score` | float (0-1) | Freshness of retrieved docs (higher = newer) |
| `similarity_score` | float (0-1) | Mean cosine similarity from RAG |
| `data_coverage_score` | float (0-1) | Retrieved docs / requested (5/5 = 1.0) |
| `platform_stability_score` | float (0-1) | 1.0 for ≤3 platforms, penalized above |
| **Phase 6 Drift** | | |
| `drift_similarity` | float (-1 to 1) | Cosine similarity vs. previous strategy |
| `drift_level` | string | `"LOW"`, `"MODERATE"`, or `"HIGH"` |
| `regenerate_flag` | bool | True = HIGH drift, version incremented |

### Confidence Formula (Phase 5)
```
confidence = 0.4 × trend_recency
           + 0.3 × similarity
           + 0.2 × data_coverage
           + 0.1 × platform_stability
```

### Drift Decision Logic (Phase 6)
```
drift_similarity < 0.75         → HIGH (regenerate=True, version++)
0.75 ≤ drift_similarity < 0.85  → MODERATE (monitor)
drift_similarity ≥ 0.85         → LOW (stable)
```

---

## Error Responses

### 422 - SME Profile Validation
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "business_type"],
      "msg": "Field required"
    },
    {
      "type": "string_too_short",
      "loc": ["body", "industry"],
      "msg": "String should have at least 1 character"
    }
  ]
}
```

### 502 - LLM Generation Failed
```json
{
  "detail": "Strategy generation failed: Groq API rate limit exceeded"
}
```

### 503 - RAG Retrieval Failed
```json
{
  "detail": "Knowledge retrieval failed: Database connection timeout"
}
```

---

## Typical Response Times

| Endpoint | Time | Notes |
|---|---|---|
| `/health` | <100ms | Instant |
| `/knowledge/add` | 2-5s | Embedding generation |
| `/strategy/generate` | 15-30s | RAG + LLM + confidence + drift |

**First request may take 30-60s** while sentence-transformers model downloads (~120MB).

---

## Sample cURL Commands

### Health Check
```bash
curl http://localhost:8000/health
```

### Add Knowledge
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Instagram Reels prioritized in 2026 algorithm",
    "source_type": "algorithm_update",
    "platform": "instagram",
    "industry": "digital_marketing"
  }'
```

### Generate Strategy (minimal)
```bash
curl -X POST http://localhost:8000/api/v1/strategy/generate \
  -H "Content-Type: application/json" \
  -d '{
    "business_type": "Cafe",
    "industry": "Food & Beverage",
    "business_size": "micro",
    "business_stage": "growth",
    "location": {"city": "Kuala Lumpur", "country": "Malaysia"},
    "products_services": "Specialty coffee",
    "unique_selling_proposition": "Eco-friendly",
    "monthly_budget": 1500,
    "has_marketing_team": false,
    "content_creation_capacity": ["photos"],
    "primary_goal": "increase_foot_traffic",
    "demographics": {
      "age_range": "25_34",
      "gender": ["all"],
      "income_level": "middle_income"
    },
    "target_location": "Urban KL",
    "interests": ["coffee"],
    "preferred_platforms": ["Instagram"],
    "current_platforms": ["Instagram"],
    "challenges": ["limited_budget"],
    "strengths": ["unique_product"]
  }'
```
