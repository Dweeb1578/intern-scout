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

def _evil():
    job = Job("=cmd|' /C calc'!A1", "@SUM(1+9)", "SF",
              True, "http://x/1", "pipe | break\nnewline", "greenhouse")
    return RankedJob(job=job, score=1.0, reason="-2+3")

def test_csv_neutralizes_formula_injection(tmp_path):
    p = tmp_path / "evil.csv"
    to_csv([_evil()], str(p))
    rows = list(csv.DictReader(p.open()))
    # leading formula triggers are prefixed with a quote so spreadsheets treat as text
    assert rows[0]["title"].startswith("'=")
    assert rows[0]["company"].startswith("'@")
    assert rows[0]["reason"].startswith("'-")

def test_markdown_escapes_pipes_and_newlines(tmp_path):
    p = tmp_path / "evil.md"
    to_markdown([_evil()], str(p))
    # every data row must keep exactly the 8-column structure (9 pipes), so a stray
    # pipe in a cell can't inject extra columns, and no raw newline splits the row
    data_lines = [ln for ln in p.read_text().splitlines() if ln.startswith("| ") and "---" not in ln]
    body = data_lines[-1]
    assert "\\|" in body                          # the stray pipe got escaped
    assert body.replace("\\|", "").count("|") == 9  # only 9 real column separators remain
