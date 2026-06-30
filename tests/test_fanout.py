from internscout.config import load_config
from internscout.fanout import fan_out, _fallback_fanout, FanOut

def test_fallback_extracts_keywords():
    fo = _fallback_fanout("backend engineering internship at an AI startup")
    assert "backend" in fo.keywords
    assert any("intern" in q for q in fo.search_queries)
    assert isinstance(fo, FanOut)

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
