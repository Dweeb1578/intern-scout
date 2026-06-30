import logging
from ..models import Job, Filters
from .base import is_intern_role, detect_remote, location_param

log = logging.getLogger(__name__)

class IndeedSource:
    name = "indeed"

    def parse_results(self, html: str) -> list[Job]:
        from scrapling.parser import Selector
        page = Selector(html, url="https://www.indeed.com")
        out = []
        for card in page.css("div.job_seen_beacon"):
            # Indeed's card markup rotates; try current selectors then older ones
            title = (card.css("span[id^=jobTitle]::text").get()
                     or card.css("h2.jobTitle span::text").get() or "").strip()
            if not is_intern_role(title):
                continue
            company = (card.css("[data-testid=company-name]::text").get()
                       or card.css("span.companyName::text").get() or "").strip()
            loc = (card.css("[data-testid=text-location]::text").get()
                   or card.css("div.companyLocation::text").get() or "").strip()
            jk = card.css("a[data-jk]::attr(data-jk)").get()
            if jk:
                url = f"https://www.indeed.com/viewjob?jk={jk}"
            else:
                href = (card.css("h3.jobTitle a::attr(href)").get()
                        or card.css("a.jcs-JobTitle::attr(href)").get() or "")
                url = ("https://www.indeed.com" + href) if href.startswith("/") else href
            out.append(Job(title=title, company=company, location=loc,
                           remote=detect_remote(loc), url=url,
                           description=title, source=self.name))
        return out

    def search(self, queries: list[str], filters: Filters) -> list[Job]:
        from scrapling.fetchers import StealthyFetcher
        from urllib.parse import quote_plus
        from ..geo import is_india_location
        loc = location_param(filters)
        # Indeed is country-domained: www.indeed.com serves US results and ignores
        # an India `l=` param, so route Indian searches through in.indeed.com.
        domain = "in.indeed.com" if loc and is_india_location(loc) else "www.indeed.com"
        out = []
        for q in queries[:2]:
            url = f"https://{domain}/jobs?q={quote_plus(q)}"
            if loc:
                url += f"&l={quote_plus(loc)}"
            try:
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True)
                out.extend(self.parse_results(page.html_content))
            except Exception as e:
                log.warning("indeed query %r failed (best-effort): %s", q, e)
        return out
