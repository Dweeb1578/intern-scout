import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import UserQuery, Filters, Job
from .fanout import fan_out
from .matcher import rank
from .sources.base import dedupe

log = logging.getLogger(__name__)

# A company name scraped off YC is only a *guess* at that company's ATS slug, and
# every guess costs one HTTP request on each of the three ATS sources. Cap it so a
# big YC page can't turn into hundreds of 404s.
MAX_DISCOVERED_SLUGS = 40

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
    """Run one source, giving up after `timeout` seconds.

    Deliberately a bare daemon thread rather than a ThreadPoolExecutor: the
    executor's context manager (and its atexit hook) join their workers, so a
    wedged source would still block for its full duration despite the timeout,
    and could then keep the interpreter alive on the way out. A daemon thread we
    can simply walk away from.
    """
    name = getattr(src, "name", src)
    result: list = []
    failure: list = []

    def work() -> None:
        try:
            result.extend(src.search(queries, filters) or [])
        except BaseException as e:            # noqa: BLE001 - never kill the run
            failure.append(e)

    t = threading.Thread(target=work, name=f"internscout-{name}", daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        log.warning("source %s timed out after %ss", name, timeout)
        return []
    if failure:
        log.warning("source %s failed: %s", name, failure[0])
        return []
    return result

def collect(sources, queries, filters, timeout) -> list:
    jobs: list = []
    yc = next((s for s in sources if getattr(s, "name", "") == "yc"), None)
    rest = [s for s in sources if s is not yc]
    discovered: list = []
    if yc is not None:
        jobs.extend(_safe_search(yc, queries, filters, timeout))
        discovered = list(getattr(yc, "discovered_slugs", []))[:MAX_DISCOVERED_SLUGS]
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
