from app.agents.profile_builder import build_profile

def test_basic_profile():
    raw = "Small spa in Galle. Budget 30k. Target women 25-45. Prefer Facebook and Instagram."
    profile = build_profile(raw)
    assert "business_identity" in profile
    assert profile["resources"]["monthly_budget"] != ""
