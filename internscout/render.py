import csv
from .models import RankedJob

_COLS = ["rank", "score", "title", "company", "location", "source", "reason", "url"]

# Scraped job fields are untrusted. Neutralize spreadsheet/markdown injection before
# writing them to files a user opens in Excel/Sheets or renders as Markdown.
_CSV_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")

def _csv_safe(value):
    """Prefix a leading formula trigger with ' so spreadsheets treat it as text."""
    if isinstance(value, str) and value and value[0] in _CSV_TRIGGERS:
        return "'" + value
    return value

def _md_safe(value):
    """Escape pipes and collapse newlines so a cell can't break the table."""
    if not isinstance(value, str):
        return value
    return (value.replace("\\", "\\\\").replace("|", "\\|")
            .replace("\r", " ").replace("\n", " ")
            .replace("<", "&lt;").replace(">", "&gt;"))

def _rows(ranked: list[RankedJob]):
    for i, r in enumerate(ranked, 1):
        j = r.job
        yield {"rank": i, "score": round(r.score, 1), "title": j.title,
               "company": j.company, "location": j.location, "source": j.source,
               "reason": r.reason, "url": j.url}

def render_table(ranked: list[RankedJob]) -> None:
    from rich.console import Console
    from rich.table import Table
    t = Table(show_lines=False)
    for c in ["#", "Score", "Title", "Company", "Location", "Src", "Why", "URL"]:
        t.add_column(c, overflow="fold")
    for row in _rows(ranked):
        t.add_row(str(row["rank"]), str(row["score"]), row["title"], row["company"],
                  row["location"], row["source"], row["reason"], row["url"])
    Console().print(t)

def to_csv(ranked: list[RankedJob], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_COLS)
        w.writeheader()
        for row in _rows(ranked):
            w.writerow({k: _csv_safe(v) for k, v in row.items()})

def to_markdown(ranked: list[RankedJob], path: str) -> None:
    lines = ["| # | Score | Title | Company | Location | Source | Why | URL |",
             "|---|---|---|---|---|---|---|---|"]
    for row in _rows(ranked):
        safe = {k: _md_safe(v) for k, v in row.items()}
        lines.append("| {rank} | {score} | {title} | {company} | {location} | "
                     "{source} | {reason} | {url} |".format(**safe))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def export(ranked, fmt: str, path: str | None) -> str | None:
    if fmt == "csv":
        path = path or "results.csv"; to_csv(ranked, path); return path
    if fmt == "md":
        path = path or "results.md"; to_markdown(ranked, path); return path
    return None
