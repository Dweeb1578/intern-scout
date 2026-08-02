import logging
from ..models import Job, Filters
from .base import is_intern_role, detect_remote, location_param, BROWSER_TIMEOUT_MS

log = logging.getLogger(__name__)

class IndeedSource:
    name = "indeed"

    def parse_results(self, html: str, domain: str = "www.indeed.com") -> list[Job]:
        from scrapling.parser import Selector
        # Job links must stay on the domain the search ran against: an Indian
        # result rehomed onto www.indeed.com bounces through a country redirect.
        base = f"https://{domain}"
        page = Selector(html, url=base)
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
                url = f"{base}/viewjob?jk={jk}"
            else:
                href = (card.css("h3.jobTitle a::attr(href)").get()
                        or card.css("a.jcs-JobTitle::attr(href)").get() or "")
                url = (base + href) if href.startswith("/") else href
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
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True,
                                             timeout=BROWSER_TIMEOUT_MS)
                out.extend(self.parse_results(page.html_content, domain))
            except Exception as e:
                log.warning("indeed query %r failed (best-effort): %s", q, e)
        return out
