from pathlib import Path
from internscout.sources.yc import YCSource

FIX = Path(__file__).parent / "fixtures" / "yc_jobs.html"

def test_parse_listing_filters_interns_and_collects_slugs():
    src = YCSource()
    jobs = src.parse_listing(FIX.read_text())
    assert len(jobs) == 1
    assert jobs[0].title == "Software Engineer Intern"
    assert jobs[0].company == "acmeai"
    assert jobs[0].remote is True
    assert jobs[0].source == "yc"
    assert "acmeai" in src.discovered_slugs
