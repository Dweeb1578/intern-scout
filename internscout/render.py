import csv
from .models import RankedJob

_COLS = ["rank", "score", "title", "company", "location", "source", "reason", "url"]

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
            w.writerow(row)

def to_markdown(ranked: list[RankedJob], path: str) -> None:
    lines = ["| # | Score | Title | Company | Location | Source | Why | URL |",
             "|---|---|---|---|---|---|---|---|"]
    for row in _rows(ranked):
        lines.append("| {rank} | {score} | {title} | {company} | {location} | "
                     "{source} | {reason} | {url} |".format(**row))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def export(ranked, fmt: str, path: str | None) -> str | None:
    if fmt == "csv":
        path = path or "results.csv"; to_csv(ranked, path); return path
    if fmt == "md":
        path = path or "results.md"; to_markdown(ranked, path); return path
    return None
