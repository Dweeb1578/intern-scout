import json
from pathlib import Path
from internscout.models import Filters
from internscout.sources.greenhouse import GreenhouseSource

FIX = Path(__file__).parent / "fixtures" / "greenhouse_acme.json"

def test_parse_board_keeps_only_interns():
    payload = json.loads(FIX.read_text())
    jobs = GreenhouseSource().parse_board("acme", payload)
    assert len(jobs) == 1
    j = jobs[0]
    assert j.title == "Software Engineering Intern"
    assert j.company == "acme"
    assert j.source == "greenhouse"
    assert j.remote is True
    assert j.url.endswith("/jobs/1")
