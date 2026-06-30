from pathlib import Path
from internscout.sources.indeed import IndeedSource

FIX = Path(__file__).parent / "fixtures" / "indeed_results.html"

def test_parse_results_keeps_interns_with_current_selectors():
    jobs = IndeedSource().parse_results(FIX.read_text())
    assert len(jobs) == 1
    j = jobs[0]
    assert j.title == "Operations Intern"
    assert j.company == "Acme Logistics"
    assert j.location == "Mumbai, India"
    assert "abc123" in j.url            # url built from the data-jk
    assert j.source == "indeed"
