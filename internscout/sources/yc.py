import logging
from ..models import Job, Filters
from .base import is_intern_role, detect_remote

log = logging.getLogger(__name__)

class YCSource:
    name = "yc"

    def __init__(self):
        self.discovered_slugs: list[str] = []

    def parse_listing(self, html: str) -> list[Job]:
        from scrapling.parser import Selector
        page = Selector(html, url="https://www.workatastartup.com")
        out = []
        for el in page.css("div.job"):
            title = (el.css("a.job-title::text").get() or "").strip()
            if not is_intern_role(title):
                continue
            company = (el.css("span.company::text").get() or "").strip()
            loc = (el.css("span.location::text").get() or "").strip()
            desc = (el.css("p.desc::text").get() or "").strip()
            url = el.css("a.job-title::attr(href)").get() or ""
            if company and company not in self.discovered_slugs:
                self.discovered_slugs.append(company)
            out.append(Job(title=title, company=company, location=loc,
                           remote=detect_remote(f"{loc} {desc}"), url=url,
                           description=desc, source=self.name))
        return out

    def search(self, queries: list[str], filters: Filters) -> list[Job]:
        from scrapling.fetchers import StealthyFetcher
        from urllib.parse import quote_plus
        out = []
        for q in queries[:3]:
            url = f"https://www.workatastartup.com/jobs?query={quote_plus(q)}"
            try:
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
                out.extend(self.parse_listing(page.html_content))
            except Exception as e:
                log.warning("yc query %r failed: %s", q, e)
        return out
