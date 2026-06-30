import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import UserQuery, Filters, Job
from .fanout import fan_out
from .matcher import rank
from .sources.base import dedupe

log = logging.getLogger(__name__)

def build_sources():
    from .sources.greenhouse import GreenhouseSource
    from .sources.lever import LeverSource
    from .sources.ashby import AshbySource
    from .sources.yc import YCSource
    from .sources.linkedin import LinkedInSource
    from .sources.indeed import IndeedSource
    return [GreenhouseSource(), LeverSource(), AshbySource(),
            YCSource(), LinkedInSource(), IndeedSource()]

def _safe_search(src, queries, filters, timeout) -> list:
    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(src.search, queries, filters).result(timeout=timeout)
    except Exception as e:
        log.warning("source %s failed: %s", getattr(src, "name", src), e)
        return []

def collect(sources, queries, filters, timeout) -> list:
    jobs: list = []
    yc = next((s for s in sources if getattr(s, "name", "") == "yc"), None)
    rest = [s for s in sources if s is not yc]
    discovered: list = []
    if yc is not None:
        jobs.extend(_safe_search(yc, queries, filters, timeout))
        discovered = list(getattr(yc, "discovered_slugs", []))
    for s in rest:
        if hasattr(s, "extra_slugs"):
            s.extra_slugs = discovered
    with ThreadPoolExecutor(max_workers=min(8, len(rest) or 1)) as ex:
        futs = {ex.submit(_safe_search, s, queries, filters, timeout): s for s in rest}
        for f in as_completed(futs):
            jobs.extend(f.result())
    return dedupe(jobs)

def run(query: UserQuery, cfg, sources=None):
    sources = sources if sources is not None else build_sources()
    fo = fan_out(query.prompt, cfg)
    jobs = collect(sources, fo.search_queries or [query.prompt], query.filters,
                   cfg.per_source_timeout)
    return rank(jobs, query, fo, cfg)
