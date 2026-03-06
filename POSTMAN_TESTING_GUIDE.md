# Postman Collection Testing Guide

## Import Collection

1. Open Postman
2. Click **Import** (top left)
3. Select `postman_collection.json`
4. Collection will appear as "Marketing Strategy Recommender API"

---

## Prerequisites

### 1. Start Backend Server
```powershell
cd d:\Projects\marketing-stratergy-recommender
uvicorn app.main:app --reload --port 8000
```

Wait for: `Application initialized — Marketing Strategy Recommender v1.0.0`

### 2. Run Database Migrations

**Supabase SQL Editor** (run in order):
- `migrations/001_initial_schema.sql`
- `migrations/002_phase2_rag.sql`
- `migrations/003_phase5_advanced_confidence.sql`
- `migrations/004_phase6_drift.sql`

---

## Test Sequence

### Step 1: Health Check
**Endpoint:** `GET /health`

**Expected Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-05T..."
}
```

✅ **Pass:** Backend is running  
❌ **Fail:** Check if server is started

---

### Step 2: Seed Knowledge Base

Run these requests in order (all should return **HTTP 200**):

1. **Add Knowledge - Algorithm Update**
2. **Add Knowledge - Case Study (F&B)**
3. **Add Knowledge - Research Finding**
4. **Add Knowledge - Best Practice**
5. **Add Knowledge - Budget Guide**
6. **Add Knowledge - Sustainability Trend**

**Expected Response (each):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid",
    "content": "...",
    "source_type": "...",
    "platform": "...",
    "industry": "...",
    "created_at": "2026-03-05T..."
  }
}
```

**What's happening:**
- Content is being embedded (384-dimensional vector)
- Stored in `knowledge_base` table with pgvector
- Available for RAG retrieval

**Verify in Supabase:**
```sql
SELECT count(*), source_type 
FROM knowledge_base 
GROUP BY source_type;
```

---

### Step 3: Generate Strategies

Run these in order to test different scenarios:

#### 3.1 Urban Cafe (Full Profile)
**Time:** ~15-30 seconds  
**Expected:** Full strategy with high confidence (>0.7) if knowledge base is seeded

**Key checks:**
```json
{
  "strategy_summary": "...",
  "recommended_platforms": ["Instagram", "Facebook", "WhatsApp Business"],
  "content_strategy": "...",
  "budget_allocation": {
    "Instagram Ads": 35.0,
    "Facebook Ads": 25.0,
    "Content Creation": 30.0,
    "WhatsApp Tools": 10.0
  },
  "reasoning": "...",  // Should cite retrieved knowledge
  "confidence_score": 0.82,  // Should be >0.7 with good knowledge
  "version": 1,
  "is_outdated": false,
  
  // Phase 5 confidence breakdown
  "trend_recency_score": 0.95,  // Higher = fresher docs
  "similarity_score": 0.78,     // Higher = better RAG match
  "data_coverage_score": 1.0,   // 5/5 docs retrieved
  "platform_stability_score": 1.0,  // ≤3 platforms = stable
  
  // Phase 6 drift metadata (null on first generation)
  "drift_similarity": null,
  "drift_level": null,
  "regenerate_flag": null
}
```

#### 3.2 Retail Store (Minimal Profile)
**Purpose:** Test with minimal required fields  
**Expected:** Strategy generates but confidence may be lower

#### 3.3 Service Business (B2B)
**Purpose:** Test LinkedIn + professional service context  
**Expected:** Different platform mix, B2B-focused strategy

---

## What Each Phase Does

### Phase 1-2: Basic Pipeline
- ✅ RAG retrieval from knowledge base
- ✅ LLM strategy generation via Groq
- ✅ Structured JSON response

### Phase 3-4: Expanded Profile
- ✅ 35+ field SME profile support
- ✅ 8-section form compatibility
- ✅ Basic confidence scoring

### Phase 5: Advanced Confidence
- ✅ **Trend Recency:** Freshness of retrieved docs (exp decay)
- ✅ **Similarity:** Mean cosine similarity from RAG
- ✅ **Data Coverage:** Retrieved docs / requested ratio
- ✅ **Platform Stability:** Penalty for >3 platforms

### Phase 6: Drift Detection
- ✅ **Cosine Similarity:** Strategy vs. context embedding
- ✅ **Drift Levels:** LOW / MODERATE / HIGH
- ✅ **Auto Versioning:** Increment on HIGH drift
- ✅ **Regeneration Flag:** When to force new strategy

---

## Testing Drift Detection

Run the **same request twice**:

**First call:**
```json
{
  "version": 1,
  "drift_similarity": null,
  "drift_level": null
}
```

**Second call (immediate):**
```json
{
  "version": 1,  // No version bump (LOW drift)
  "drift_similarity": 0.94,  // Very similar context
  "drift_level": "LOW"
}
```

**To trigger HIGH drift:**
1. Add 10+ new knowledge entries with different content
2. Or change SME profile significantly (different industry/platforms)
3. Re-run strategy generation
4. Should see `"drift_level": "HIGH"` and version increment

---

## Common Issues

### Issue: `HTTP 422 - Validation Error`
**Cause:** Missing required fields or wrong data types  
**Fix:** Check request body matches `SMEProfile` model

### Issue: `HTTP 503 - Service Unavailable`
**Cause:** Cannot reach Supabase  
**Fix:** Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`

### Issue: `HTTP 500 - Embedding generation failed`
**Cause:** sentence-transformers model not loaded  
**Fix:** First request takes 10-20s to download model, retry

### Issue: Low confidence score (<0.5)
**Cause:** Empty or irrelevant knowledge base  
**Fix:** Add 20+ knowledge entries matching the SME's industry/platform

### Issue: Strategy too generic
**Cause:** RAG not finding relevant documents  
**Fix:** 
- Ensure knowledge entries use rich, specific content
- Add platform and industry metadata
- Wait for Phase 7 hybrid filtering

---

## Success Criteria

| Component | Pass Criteria |
|---|---|
| Health Check | Returns 200 |
| Knowledge Add | 6/6 insertions succeed |
| Strategy Generation | Completes in <30s |
| Confidence Score | >0.7 with seeded knowledge |
| Trend Recency | >0.8 with recent docs |
| Similarity Score | >0.6 (good RAG match) |
| Drift Detection | Second call shows drift metadata |
| Budget Allocation | Sums to ~100% |
| Platform Recommendations | Matches preferred_platforms from profile |

---

## Next Steps After Testing

1. ✅ All tests pass → Deploy to Railway/Render
2. ⚠️ Low confidence → Add more knowledge entries via n8n
3. ⚠️ Generic strategies → Implement Phase 7 hybrid filtering
4. ✅ Ready for production → Connect frontend
