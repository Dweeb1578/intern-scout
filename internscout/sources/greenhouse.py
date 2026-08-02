import json
import logging
from ..models import Job, Filters
from .base import is_intern_role, detect_remote, HTTP_TIMEOUT_S

log = logging.getLogger(__name__)

class GreenhouseSource:
    name = "greenhouse"

    def __init__(self):
        self.extra_slugs: list[str] = []

    def parse_board(self, slug: str, payload: dict) -> list[Job]:
        out = []
        for j in payload.get("jobs", []):
            title = j.get("title", "")
            if not is_intern_role(title):
                continue
            content = j.get("content", "") or ""
            loc = (j.get("location") or {}).get("name", "")
            out.append(Job(
                title=title, company=slug, location=loc,
                remote=detect_remote(f"{loc} {content}"),
                url=j.get("absolute_url", ""), description=content,
                source=self.name, posted_at=j.get("updated_at"),
            ))
        return out

    def _slugs(self):
        from ..config import load_config
        seed = json.loads(load_config().seed_path.read_text())
        slugs = [s["slug"] for s in seed if s.get("ats") == "greenhouse"]
        return list(dict.fromkeys(slugs + self.extra_slugs))

    def _fetch_json(self, url: str) -> dict:
        from scrapling.fetchers import Fetcher
        return Fetcher.get(url, timeout=HTTP_TIMEOUT_S).json()

    def search(self, queries: list[str], filters: Filters) -> list[Job]:
        out = []
        for slug in self._slugs():
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            try:
                out.extend(self.parse_board(slug, self._fetch_json(url)))
            except Exception as e:
                log.warning("greenhouse %s failed: %s", slug, e)
        return out
