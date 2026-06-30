from internscout.models import Job, Filters, UserQuery
from internscout.config import load_config
from internscout.pipeline import collect, run

class FakeSource:
    def __init__(self, name, jobs, boom=False):
        self.name = name; self._jobs = jobs; self._boom = boom
    def search(self, queries, filters):
        if self._boom:
            raise RuntimeError("blocked")
        return self._jobs

def mkjob(title, url):
    return Job(title=title, company="C", location="Remote", remote=True,
               url=url, description="python backend", source="s")

def test_collect_is_fail_soft_and_dedupes():
    s1 = FakeSource("a", [mkjob("SWE Intern", "u1"), mkjob("SWE Intern", "u1")])
    s2 = FakeSource("b", [], boom=True)
    out = collect([s1, s2], ["x"], Filters(), timeout=5)
    assert len(out) == 1  # deduped, and s2 blowing up did not crash

def test_run_end_to_end_keyword_mode(monkeypatch):
    monkeypatch.setenv("INTERNSCOUT_MATCHER", "keyword")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    cfg = load_config()
    src = FakeSource("a", [mkjob("Backend Intern", "u1"), mkjob("Sales Intern", "u2")])
    q = UserQuery("backend intern python", Filters(max_results=10))
    ranked = run(q, cfg, sources=[src])
    assert ranked and ranked[0].job.title == "Backend Intern"
