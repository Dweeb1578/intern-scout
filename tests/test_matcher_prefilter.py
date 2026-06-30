from internscout.models import Job, Filters
from internscout.fanout import FanOut
from internscout.matcher import keyword_prefilter, passes_filters

def mkjob(**kw):
    base = dict(title="SWE Intern", company="Acme", location="San Francisco, CA",
                remote=False, url="u", description="python backend api", source="s")
    base.update(kw); return Job(**base)

def test_keyword_match_keeps_relevant():
    fo = FanOut(search_queries=[], keywords=["backend", "api"], domain_tags=[])
    jobs = [mkjob(), mkjob(title="Sales Intern", description="cold calling")]
    out = keyword_prefilter(jobs, fo, Filters())
    assert len(out) == 1 and out[0].title == "SWE Intern"

def test_remote_filter():
    assert passes_filters(mkjob(remote=True), Filters(remote="remote"))
    assert not passes_filters(mkjob(remote=False), Filters(remote="remote"))
    assert passes_filters(mkjob(remote=False), Filters(remote="onsite"))

def test_location_filter():
    f = Filters(locations=["New York"])
    assert not passes_filters(mkjob(location="San Francisco, CA"), f)
    assert passes_filters(mkjob(location="New York, NY"), f)

def test_empty_keywords_keeps_all():
    fo = FanOut(search_queries=[], keywords=[], domain_tags=[])
    jobs = [mkjob(), mkjob(title="Sales")]
    assert len(keyword_prefilter(jobs, fo, Filters())) == 2

def test_india_filter_matches_indian_cities():
    f = Filters(locations=["India"])
    # literal country, and Indian cities that don't contain the word "India"
    assert passes_filters(mkjob(location="Bengaluru, KA"), f)
    assert passes_filters(mkjob(location="Gurgaon"), f)
    assert passes_filters(mkjob(location="Remote - India"), f)
    # a non-Indian onsite role is rejected
    assert not passes_filters(mkjob(location="San Francisco, CA"), f)

def test_india_filter_still_keeps_remote_anywhere():
    f = Filters(locations=["India"])
    # remote roles always pass the location filter, even if onsite-location is elsewhere
    assert passes_filters(mkjob(location="London, UK", remote=True), f)
