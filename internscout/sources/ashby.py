import json
import logging
from ..models import Job, Filters
from .base import is_intern_role, detect_remote

log = logging.getLogger(__name__)

class AshbySource:
    name = "ashby"

    def __init__(self):
        self.extra_slugs: list[str] = []

    def parse_board(self, slug: str, payload: dict) -> list[Job]:
        out = []
        for j in payload.get("jobs", []):
            title = j.get("title", "")
            if not (is_intern_role(title) or is_intern_role(j.get("employmentType", ""))):
                continue
            loc = j.get("location", "") or ""
            desc = j.get("descriptionPlain") or j.get("description") or ""
            remote = j.get("isRemote")
            if remote is None:
                remote = detect_remote(f"{loc} {desc}")
            out.append(Job(
                title=title, company=slug, location=loc, remote=remote,
                url=j.get("jobUrl", ""), description=desc, source=self.name,
            ))
        return out

    def _slugs(self):
        from ..config import load_config
        seed = json.loads(load_config().seed_path.read_text())
        slugs = [s["slug"] for s in seed if s.get("ats") == "ashby"]
        return list(dict.fromkeys(slugs + self.extra_slugs))

    def _fetch_json(self, url: str) -> dict:
        from scrapling.fetchers import Fetcher
        return Fetcher.get(url).json()

    def search(self, queries, filters) -> list[Job]:
        out = []
        for slug in self._slugs():
            try:
                out.extend(self.parse_board(slug, self._fetch_json(
                    f"https://api.ashbyhq.com/posting-api/job-board/{slug}")))
            except Exception as e:
                log.warning("ashby %s failed: %s", slug, e)
        return out
