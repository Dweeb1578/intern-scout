import json
import logging
from ..models import Job, Filters
from .base import is_intern_role, detect_remote

log = logging.getLogger(__name__)

class LeverSource:
    name = "lever"

    def __init__(self):
        self.extra_slugs: list[str] = []

    def parse_board(self, slug: str, payload: list) -> list[Job]:
        out = []
        for j in payload:
            title = j.get("text", "")
            cats = j.get("categories") or {}
            commitment = cats.get("commitment", "") or ""
            if not (is_intern_role(title) or is_intern_role(commitment)):
                continue
            loc = cats.get("location", "") or ""
            desc = j.get("descriptionPlain", "") or ""
            out.append(Job(
                title=title, company=slug, location=loc,
                remote=detect_remote(f"{loc} {desc}"),
                url=j.get("hostedUrl", ""), description=desc, source=self.name,
            ))
        return out

    def _slugs(self):
        from ..config import load_config
        seed = json.loads(load_config().seed_path.read_text())
        slugs = [s["slug"] for s in seed if s.get("ats") == "lever"]
        return list(dict.fromkeys(slugs + self.extra_slugs))

    def _fetch_json(self, url: str):
        from scrapling.fetchers import Fetcher
        return json.loads(Fetcher.fetch(url).body)

    def search(self, queries, filters) -> list[Job]:
        out = []
        for slug in self._slugs():
            try:
                out.extend(self.parse_board(slug, self._fetch_json(
                    f"https://api.lever.co/v0/postings/{slug}?mode=json")))
            except Exception as e:
                log.warning("lever %s failed: %s", slug, e)
        return out
