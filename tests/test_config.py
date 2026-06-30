import os
from internscout.config import load_config, has_llm

def test_load_config_defaults(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    cfg = load_config()
    assert cfg.groq_api_key is None
    assert cfg.matcher_mode == "hybrid"
    assert cfg.per_source_timeout == 30
    assert has_llm(cfg) is False

def test_has_llm_true(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    cfg = load_config()
    assert cfg.groq_api_key == "gsk_test"
    assert has_llm(cfg) is True
