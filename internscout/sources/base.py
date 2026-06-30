from typing import Protocol
import re
from ..models import Job, Filters

class Source(Protocol):
    name: str
    def search(self, queries: list[str], filters: Filters) -> list[Job]: ...

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
