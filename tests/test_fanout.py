from internscout.config import load_config
from internscout.fanout import fan_out, _fallback_fanout, FanOut

def test_fallback_extracts_keywords():
    fo = _fallback_fanout("backend engineering internship at an AI startup")
    assert "backend" in fo.keywords
    assert any("intern" in q for q in fo.search_queries)
    assert isinstance(fo, FanOut)

def test_fallback_expands_business_domains():
    # operations / GTM / supply-chain / management prompts must fan out into
    # domain vocabulary so keyword mode (no API key) catches relevant JDs
    ops = _fallback_fanout("operations internship")
    assert "fulfillment" in ops.keywords or "process" in ops.keywords
    gtm = _fallback_fanout("gtm internship")
    assert "sales" in gtm.keywords or "go-to-market" in gtm.keywords
    sc = _fallback_fanout("supply chain internship")
    assert "procurement" in sc.keywords or "logistics" in sc.keywords
    mgmt = _fallback_fanout("management trainee role")
    assert "business analyst" in mgmt.keywords or "chief of staff" in mgmt.keywords

def test_fan_out_uses_fallback_without_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    cfg = load_config()
    fo = fan_out("data science intern", cfg)
    assert fo.search_queries  # non-empty
    assert "data" in fo.keywords or "science" in fo.keywords

def test_fan_out_uses_llm_when_provided(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    cfg = load_config()
    def fake_llm(system, user):
        return '{"search_queries": ["ml intern"], "keywords": ["ml","pytorch"], "domain_tags": ["ai"]}'
    fo = fan_out("ml intern", cfg, llm=fake_llm)
    assert fo.search_queries == ["ml intern"]
    assert "pytorch" in fo.keywords
