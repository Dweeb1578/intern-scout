from internscout.models import Job, Filters, UserQuery
from internscout.config import load_config
from internscout.pipeline import run

class Fake:
    name = "fake"
    def search(self, queries, filters):
        return [
            Job("Backend Engineering Intern", "Acme", "Remote", True, "http://x/1",
                "Build Python APIs and services.", "greenhouse"),
            Job("Marketing Intern", "Acme", "NYC", False, "http://x/2",
                "Run social campaigns.", "greenhouse"),
        ]

def test_offline_pipeline_returns_ranked(monkeypatch):
    monkeypatch.setenv("INTERNSCOUT_MATCHER", "keyword")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    cfg = load_config()
    q = UserQuery("backend python internship", Filters(max_results=10))
    ranked = run(q, cfg, sources=[Fake()])
    assert ranked
    assert ranked[0].job.title == "Backend Engineering Intern"
