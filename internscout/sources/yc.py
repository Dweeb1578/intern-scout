import logging
import re
from ..models import Job, Filters
from .base import is_intern_role, detect_remote, slugify, BROWSER_TIMEOUT_MS

log = logging.getLogger(__name__)

YC_BASE = "https://www.workatastartup.com"

# "Seeing Systems\xa0(W26)" -> "Seeing Systems"
_BATCH_RE = re.compile(r"\s*\((?:[WSFXP]\d{2}|IK\d*)\)\s*$", re.I)
# a details chip that is a pay range, not a place: "$124K - $188K CAD"
_PAY_RE = re.compile(r"[$€£₹]|\d\s*K\b", re.I)
# employment-type chip that precedes the location
_EMPLOYMENT_RE = re.compile(
    r"^(intern|fulltime|full[- ]?time|parttime|part[- ]?time|contract|co[- ]?founder)$", re.I)


def _clean_company(text: str) -> str:
    """Strip YC's batch suffix and the non-breaking space in front of it."""
    return _BATCH_RE.sub("", (text or "").replace("\xa0", " ")).strip()


def _pick_location(details: list[str]) -> str:
    """Pull the place out of a card's detail chips.

    YC renders them in order: employment type, location, role category, pay
    ("Intern", "London, England, GB", "Full stack", "£2K - £3K GBP / monthly").
    Skip the type and pay chips rather than trusting a fixed index, since cards
    with no location shift everything left.
    """
    for d in details:
        if _EMPLOYMENT_RE.match(d) or _PAY_RE.search(d):
            continue
        return d
    return ""


class YCSource:
    name = "yc"

    def __init__(self):
        self.discovered_slugs: list[str] = []

    def parse_listing(self, html: str) -> list[Job]:
        from scrapling.parser import Selector
        from urllib.parse import urljoin
        page = Selector(html, url=YC_BASE)
        out = []
        # Work at a Startup moved to a Tailwind card grid with no semantic class
        # names, so anchor on the URL shapes (/jobs/<id>, /companies/<slug>) which
        # are far more stable than utility classes. `div.job` is the older markup,
        # kept as a fallback the way the Indeed source handles its rotations.
        for el in page.css("div.grid > div") or page.css("div.job"):
            title = (el.css("a[href^='/jobs/']::text").get()
                     or el.css("a.job-title::text").get() or "").strip()
            if not is_intern_role(title):
                continue

            href = (el.css("a[href^='/jobs/']::attr(href)").get()
                    or el.css("a.job-title::attr(href)").get() or "")
            # YC links are root-relative ("/jobs/123"); absolutize so the URL is
            # clickable in the table and usable in an export.
            url = urljoin(YC_BASE, href) if href else ""

            company = _clean_company(el.css("a[href^='/companies/'] span.font-bold::text").get()
                                     or el.css("span.company::text").get() or "")

            details = [d.strip() for d in el.css("p.job-details span::text").getall() if d.strip()]
            if details:
                loc = _pick_location(details)
                desc = " ".join(details)
            else:                                   # legacy markup
                loc = (el.css("span.location::text").get() or "").strip()
                desc = (el.css("p.desc::text").get() or "").strip()

            # Prefer YC's own company slug from /companies/<slug> over the display
            # name; still normalized, because an ATS board slug is alphanumeric.
            company_href = el.css("a[href^='/companies/']::attr(href)").get() or ""
            slug = slugify(company_href.rsplit("/", 1)[-1] or company)
            if slug and slug not in self.discovered_slugs:
                self.discovered_slugs.append(slug)

            out.append(Job(title=title, company=company, location=loc,
                           remote=detect_remote(f"{loc} {desc}"), url=url,
                           description=desc, source=self.name))
        return out

    def search(self, queries: list[str], filters: Filters) -> list[Job]:
        from scrapling.fetchers import StealthyFetcher
        from urllib.parse import quote_plus
        out = []
        for q in queries[:3]:
            url = f"{YC_BASE}/jobs?query={quote_plus(q)}"
            try:
                page = StealthyFetcher.fetch(url, headless=True, network_idle=True,
                                             timeout=BROWSER_TIMEOUT_MS)
                out.extend(self.parse_listing(page.html_content))
            except Exception as e:
                log.warning("yc query %r failed: %s", q, e)
        return out
