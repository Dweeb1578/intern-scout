from .models import Job, Filters, RankedJob
from .fanout import FanOut
from .config import Config, has_llm

def passes_filters(job: Job, filters: Filters) -> bool:
    if filters.remote == "remote" and job.remote is not True:
        return False
    if filters.remote == "onsite" and job.remote is True:
        return False
    if filters.locations and job.remote is not True:
        loc = job.location.lower()
        if not any(l.lower() in loc for l in filters.locations):
            return False
    return True

def keyword_prefilter(jobs: list[Job], fo: FanOut, filters: Filters) -> list[Job]:
    kws = [k.lower() for k in fo.keywords]
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
        ranked = _llm_rank(survivors, query, cfg, llm)
    else:
        ranked = _keyword_score(survivors, fo)
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked[: query.filters.max_results]

def _keyword_score(jobs, fo):
    kws = [k.lower() for k in fo.keywords]
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

def _llm_rank(jobs, query, cfg, llm):
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
        out = []
        for d in data:
            i = d.get("i")
            if isinstance(i, int) and 0 <= i < len(jobs):
                out.append(RankedJob(job=jobs[i], score=float(d.get("score", 0)),
                                     reason=str(d.get("reason", ""))))
        if out:
            return out
    except Exception:
        pass
    return _keyword_score(jobs, FanOut([], [], []))
