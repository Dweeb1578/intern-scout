from .models import Job, Filters, RankedJob
from .fanout import FanOut
from .config import Config, has_llm
from .geo import is_india_location, location_scope, remote_scopes

def _location_matches(loc: str, wanted: str) -> bool:
    """A wanted location of 'india' matches Indian cities/regions, not just the
    literal word; anything else is a plain case-insensitive substring match."""
    if wanted == "india":
        return is_india_location(loc)
    return wanted in loc

def remote_role_is_reachable(job: Job, filters: Filters) -> bool:
    """Whether a remote role is one the seeker could actually hold.

    Remote roles skip the location filter, because "remote" usually means the
    company doesn't care where you sit. But plenty of postings say "fully remote
    (within the U.S.)", and those aren't open to someone searching India. Drop a
    remote role only when the posting names a region *and* none of the wanted
    locations fall in it; anything ambiguous stays visible.
    """
    scopes = remote_scopes(f"{job.location} {job.description}")
    if not scopes:
        return True                      # unrestricted, or phrasing we can't read
    wanted = {location_scope(l) for l in filters.locations}
    wanted.discard(None)
    if not wanted:
        return True                      # can't place the seeker, so don't judge
    return bool(scopes & wanted)

def passes_filters(job: Job, filters: Filters) -> bool:
    if filters.remote == "remote" and job.remote is not True:
        return False
    if filters.remote == "onsite" and job.remote is True:
        return False
    if filters.locations:
        if job.remote is True:
            return remote_role_is_reachable(job, filters)
        loc = job.location.lower()
        if not any(_location_matches(loc, l.strip().lower()) for l in filters.locations):
            return False
    return True

def _keywords(fo: FanOut) -> list[str]:
    """Lowercased keywords, ignoring anything the model returned that isn't text."""
    return [k.lower() for k in fo.keywords if isinstance(k, str) and k]

def keyword_prefilter(jobs: list[Job], fo: FanOut, filters: Filters) -> list[Job]:
    kws = _keywords(fo)
    out = []
    for j in jobs:
        if not passes_filters(j, filters):
            continue
        if kws:
            hay = f"{j.title} {j.description}".lower()
            if not any(k in hay for k in kws):
                continue
        out.append(j)
    return out

def rank(jobs, query, fo, cfg, llm=None):
    survivors = keyword_prefilter(jobs, fo, query.filters)
    use_llm = llm is not None or (cfg.matcher_mode in ("hybrid", "llm") and has_llm(cfg))
    if cfg.matcher_mode == "keyword":
        use_llm = False
    if use_llm and survivors:
        ranked = _llm_rank(survivors, query, fo, cfg, llm)
    else:
        ranked = _keyword_score(survivors, fo)
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked[: query.filters.max_results]

def _keyword_score(jobs, fo):
    kws = _keywords(fo)
    out = []
    for j in jobs:
        hay = f"{j.title} {j.description}".lower()
        n = sum(1 for k in kws if k in hay)
        out.append(RankedJob(job=j, score=float(n), reason=f"keyword match: {n} terms"))
    return out

_RANK_SYSTEM = (
    "Score how well each internship matches the seeker's prompt, 0-100. "
    "Return ONLY a JSON array of objects with keys i (index), score, reason "
    "(one short sentence). Only include jobs worth surfacing."
)

def _llm_rank(jobs, query, fo, cfg, llm):
    import json
    if llm is None:
        from .fanout import _make_groq_caller
        llm = _make_groq_caller(cfg)
    listing = "\n".join(
        f"[{i}] {j.title} @ {j.company} ({j.location}) :: {j.description[:300]}"
        for i, j in enumerate(jobs)
    )
    user = f"PROMPT: {query.prompt}\n\nJOBS:\n{listing}"
    try:
        raw = llm(_RANK_SYSTEM, user)
        data = json.loads(raw[raw.index("["):raw.rindex("]") + 1])
        out, seen = [], set()
        for d in data:
            if not isinstance(d, dict):
                continue
            i = d.get("i")
            # bool is an int subclass; True would silently index job 1
            if not isinstance(i, int) or isinstance(i, bool):
                continue
            # the model repeats indices often enough that unguarded this shows
            # the same job twice in the results table
            if not (0 <= i < len(jobs)) or i in seen:
                continue
            seen.add(i)
            try:
                score = float(d.get("score", 0))
            except (TypeError, ValueError):
                score = 0.0
            out.append(RankedJob(job=jobs[i], score=score,
                                 reason=str(d.get("reason", ""))))
        if out:
            return out
    except Exception:
        pass
    return _keyword_score(jobs, fo)
