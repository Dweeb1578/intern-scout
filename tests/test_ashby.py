import json
from pathlib import Path
from internscout.sources.ashby import AshbySource

FIX = Path(__file__).parent / "fixtures" / "ashby_linear.json"

def test_parse_uses_isremote_flag():
    payload = json.loads(FIX.read_text())
    jobs = AshbySource().parse_board("linear", payload)
    assert len(jobs) == 1
    assert jobs[0].title == "Product Design Intern"
    assert jobs[0].remote is True
    assert jobs[0].source == "ashby"
