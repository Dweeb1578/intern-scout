from internscout.models import Job, Filters, UserQuery, RankedJob

def test_filters_defaults():
    f = Filters()
    assert f.remote == "any"
    assert f.locations == []
    assert f.max_results == 25

def test_job_dedupe_key_prefers_url():
    j = Job(title="SWE Intern", company="Acme", location="SF", remote=False,
            url="https://x.com/job/1", description="d", source="greenhouse")
    assert j.dedupe_key == "https://x.com/job/1"

def test_job_dedupe_key_falls_back_to_title_company():
    j = Job(title="SWE Intern", company="Acme", location="SF", remote=False,
            url="", description="d", source="greenhouse")
    assert j.dedupe_key == "swe intern|acme"

def test_ranked_job_wraps_job():
    j = Job(title="t", company="c", location="l", remote=None, url="u",
            description="d", source="s")
    r = RankedJob(job=j, score=88.0, reason="good fit")
    assert r.score == 88.0 and r.job.title == "t"
