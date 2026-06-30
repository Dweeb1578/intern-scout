from internscout.models import Job, Filters, UserQuery
from internscout.fanout import FanOut
from internscout.config import load_config
from internscout.matcher import rank

def mkjob(title, desc="python api backend"):
    return Job(title=title, company="Acme", location="SF", remote=False,
               url="u-"+title, description=desc, source="s")

def test_keyword_mode_ranks_without_llm(monkeypatch):
    monkeypatch.setenv("INTERNSCOUT_MATCHER", "keyword")
    cfg = load_config()
    q = UserQuery("backend intern", Filters(max_results=5))
    fo = FanOut(search_queries=[], keywords=["backend", "api", "python"], domain_tags=[])
    out = rank([mkjob("SWE Intern"), mkjob("Sales Intern", "cold calls")], q, fo, cfg)
    assert out[0].job.title == "SWE Intern"
    assert out[0].score > 0

def test_llm_rank_with_stub(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("INTERNSCOUT_MATCHER", "hybrid")
    cfg = load_config()
    q = UserQuery("backend intern", Filters(max_results=5))
    fo = FanOut(search_queries=[], keywords=["backend"], domain_tags=[])
    def fake_llm(system, user):
        return '[{"i": 0, "score": 91, "reason": "strong backend fit"}]'
    out = rank([mkjob("SWE Intern")], q, fo, cfg, llm=fake_llm)
    assert out[0].score == 91 and "backend" in out[0].reason

def test_max_results_truncates(monkeypatch):
    monkeypatch.setenv("INTERNSCOUT_MATCHER", "keyword")
    cfg = load_config()
    q = UserQuery("intern", Filters(max_results=1))
    fo = FanOut(search_queries=[], keywords=["python"], domain_tags=[])
    out = rank([mkjob("A"), mkjob("B")], q, fo, cfg)
    assert len(out) == 1
