from .models import Job, Filters, RankedJob
from .fanout import FanOut

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
