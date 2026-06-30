from pathlib import Path
from internscout.sources.linkedin import LinkedInSource

FIX = Path(__file__).parent / "fixtures" / "linkedin_results.html"

def test_parse_results_keeps_interns():
    jobs = LinkedInSource().parse_results(FIX.read_text())
    assert len(jobs) == 1
    assert jobs[0].title == "Data Science Intern"
    assert jobs[0].company == "Acme AI"
    assert jobs[0].remote is True
    assert jobs[0].source == "linkedin"
