import logging
from ..models import Job, Filters
from .base import is_intern_role, detect_remote

log = logging.getLogger(__name__)

class IndeedSource:
    name = "indeed"

    def parse_results(self, html: str) -> list[Job]:
        from scrapling.parser import Selector
        page = Selector(html, url="https://www.indeed.com")
        out = []
        for card in page.css("div.job_seen_beacon"):
            title = (card.css("h2.jobTitle span::text").get() or "").strip()
            if not is_intern_role(title):
                continue
            company = (card.css("span.companyName::text").get() or "").strip()
            loc = (card.css("div.companyLocation::text").get() or "").strip()
            href = card.css("h2.jobTitle a::attr(href)").get() or ""
            url = ("https://www.indeed.com" + href) if href.startswith("/") else href
            out.append(Job(title=title, company=company, location=loc,
                           remote=detect_remote(loc), url=url,
                           description=title, source=self.name))
        return out

    def search(self, queries: list[str], filters: Filters) -> list[Job]:
        from scrapling.fetchers import StealthyFetcher
        from urllib.parse import quote_plus
        out = []
        for q in queries[:2]:
            url = f"https://www.indeed.com/jobs?q={quote_plus(q)}"
            try:
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
                out.extend(self.parse_results(page.html_content))
            except Exception as e:
                log.warning("indeed query %r failed (best-effort): %s", q, e)
        return out
