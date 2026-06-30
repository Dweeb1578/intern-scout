import json
from pathlib import Path
from internscout.sources.lever import LeverSource

FIX = Path(__file__).parent / "fixtures" / "lever_mux.json"

def test_parse_keeps_interns_and_detects_remote():
    payload = json.loads(FIX.read_text())
    jobs = LeverSource().parse_board("mux", payload)
    assert len(jobs) == 1
    assert jobs[0].title == "Backend Engineering Intern"
    assert jobs[0].remote is True
    assert jobs[0].source == "lever"
