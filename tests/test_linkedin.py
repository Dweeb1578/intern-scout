from pathlib import Path
from internscout.sources.linkedin import LinkedInSource

FIX = Path(__file__).parent / "fixtures" / "linkedin_results.html"

def test_parse_results_keeps_interns():
    jobs = LinkedInSource().parse_results(FIX.read_text())
    assert len(jobs) == 1
    assert jobs[0].title == "Data Science Intern"
    # company lives inside a nested <a> in real LinkedIn cards
    assert jobs[0].company == "Acme AI"
    assert jobs[0].location == "Bengaluru, India"
    assert jobs[0].source == "linkedin"
    # tracking query params are stripped so the same job dedupes across queries
    assert jobs[0].url == "https://www.linkedin.com/jobs/view/1"
