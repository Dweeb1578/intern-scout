import csv
from pathlib import Path
from internscout.models import Job, RankedJob
from internscout.render import to_csv, to_markdown

def mk(n):
    return RankedJob(job=Job(f"Intern {n}", "Acme", "SF", True, f"http://x/{n}",
                            "d", "greenhouse"), score=90.0 - n, reason="fits")

def test_to_csv_writes_rows(tmp_path):
    p = tmp_path / "out.csv"
    to_csv([mk(1), mk(2)], str(p))
    rows = list(csv.DictReader(p.open()))
    assert len(rows) == 2
    assert rows[0]["title"] == "Intern 1"
    assert "url" in rows[0] and "score" in rows[0]

def test_to_markdown_has_header_and_rows(tmp_path):
    p = tmp_path / "out.md"
    to_markdown([mk(1)], str(p))
    text = p.read_text()
    assert "| Score |" in text or "Score" in text
    assert "Intern 1" in text
