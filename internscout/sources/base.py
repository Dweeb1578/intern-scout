from typing import Protocol
import re
from ..models import Job, Filters

class Source(Protocol):
    name: str
    def search(self, queries: list[str], filters: Filters) -> list[Job]: ...

# Network budgets, per request. Mind the units: Scrapling's plain `Fetcher` takes
# SECONDS (default 30), while `StealthyFetcher` wraps Playwright and takes
# MILLISECONDS (default 30000). Passing the same number to both silently gives the
# browser a 30ms budget. Both sit under the pipeline's per-source timeout so a
# single slow board can't eat the whole source's budget.
HTTP_TIMEOUT_S = 15
BROWSER_TIMEOUT_MS = 25_000

_INTERN_RE = re.compile(
    r"\b(intern|internship|co-?op|new ?grad|graduate program(?:me)?|"
    r"early career|apprentice|trainee)\b", re.I)

def is_intern_role(title: str) -> bool:
    return bool(_INTERN_RE.search(title or ""))

def detect_remote(text: str):
    t = (text or "").lower()
    if "remote" in t or "work from home" in t:
        return True
    if "on-site" in t or "onsite" in t or "in office" in t or "in-office" in t:
        return False
    return None

def slugify(name: str) -> str:
    """Turn a display company name into the shape an ATS board slug takes.

    Greenhouse/Lever/Ashby board slugs are lowercase and alphanumeric
    ("Razorpay Software Private Limited" -> "razorpaysoftwareprivatelimited"),
    so a raw display name scraped off YC will never resolve. This is still only
    a guess - misses are logged and skipped by the caller.
    """
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())

def location_param(filters) -> str:
    """First concrete location to send to a search engine (skips remote/any),
    so LinkedIn/Indeed return geo-relevant results instead of global ones."""
    for l in getattr(filters, "locations", []) or []:
        s = l.strip()
        if s and s.lower() not in ("remote", "any"):
            return s
    return ""

def dedupe(jobs: list[Job]) -> list[Job]:
    seen, out = set(), []
    for j in jobs:
        if j.dedupe_key in seen:
            continue
        seen.add(j.dedupe_key)
        out.append(j)
    return out

REGISTRY: list = []

def register(src) -> None:
    REGISTRY.append(src)

def all_sources() -> list:
    return list(REGISTRY)
