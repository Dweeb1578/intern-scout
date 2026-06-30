import logging
from ..models import Job, Filters
from .base import is_intern_role, detect_remote

log = logging.getLogger(__name__)

class LinkedInSource:
    name = "linkedin"

    def parse_results(self, html: str) -> list[Job]:
        from scrapling.parser import Selector
        page = Selector(html, url="https://www.linkedin.com")
        out = []
        for card in page.css("div.base-card"):
            title = (card.css("h3.base-search-card__title::text").get() or "").strip()
            if not is_intern_role(title):
                continue
            company = (card.css("h4.base-search-card__subtitle::text").get() or "").strip()
            loc = (card.css("span.job-search-card__location::text").get() or "").strip()
            url = card.css("a.base-card__full-link::attr(href)").get() or ""
            out.append(Job(title=title, company=company, location=loc,
                           remote=detect_remote(loc), url=url,
                           description=title, source=self.name))
        return out

    def search(self, queries: list[str], filters: Filters) -> list[Job]:
        from scrapling.fetchers import StealthyFetcher
        out = []
        for q in queries[:3]:
            url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/"
                   f"search?keywords={q.replace(' ', '%20')}")
            try:
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
                out.extend(self.parse_results(page.html_content))
            except Exception as e:
                log.warning("linkedin query %r failed (best-effort): %s", q, e)
        return out
