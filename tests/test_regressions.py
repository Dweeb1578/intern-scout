"""Regressions for bugs that were live in the tool. One test per bug."""
import pathlib
import time

import pytest

from internscout.config import load_config
from internscout.fanout import FanOut, fan_out
from internscout.geo import is_india_location, remote_scopes
from internscout.matcher import _llm_rank, keyword_prefilter, passes_filters
from internscout.models import Filters, Job, UserQuery
from internscout.pipeline import _safe_search
from internscout.sources.base import slugify
from internscout.sources.indeed import IndeedSource
from internscout.sources.yc import YCSource


def _job(title="Ops Intern", company="acme", location="Bengaluru", url="u"):
    return Job(title=title, company=company, location=location, remote=None,
               url=url, description="d", source="test")


# --- per-source timeout actually bounds wall time -----------------------------
# Was: the ThreadPoolExecutor context manager joined its worker on the way out,
# so a hung source blocked for its full duration *and* the result was discarded.

class _SlowSource:
    name = "slow"

    def search(self, queries, filters):
        time.sleep(5)
        return [_job()]


def test_slow_source_is_abandoned_at_the_timeout():
    started = time.monotonic()
    out = _safe_search(_SlowSource(), ["q"], Filters(), timeout=0.5)
    elapsed = time.monotonic() - started
    assert out == []
    assert elapsed < 2.0, f"timeout did not bound wall time ({elapsed:.1f}s)"


class _AngrySource:
    name = "angry"

    def search(self, queries, filters):
        raise RuntimeError("boom")


def test_failing_source_does_not_kill_the_run():
    assert _safe_search(_AngrySource(), ["q"], Filters(), timeout=5) == []


# --- model-generated fields are not trusted to be strings ---------------------
# Was: keyword_prefilter did k.lower() on raw JSON, so a numeric keyword raised
# AttributeError and took down the whole search.

def test_prefilter_survives_non_string_keywords():
    fo = FanOut(search_queries=["x"], keywords=["backend", 2026, None, {"a": 1}],
                domain_tags=[])
    out = keyword_prefilter([_job(title="Backend Intern")], fo, Filters(locations=[]))
    assert len(out) == 1


def test_fan_out_coerces_ragged_model_json(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    cfg = load_config()
    def fake_llm(system, user):
        return ('{"search_queries": ["ml intern", 7, "ml intern"], '
                '"keywords": "pytorch", "domain_tags": null}')
    fo = fan_out("ml intern", cfg, llm=fake_llm)
    assert fo.search_queries == ["ml intern", "7"]   # coerced + de-duped
    assert fo.keywords == ["pytorch"]                # bare string wrapped
    assert fo.domain_tags == []
    assert all(isinstance(k, str) for k in fo.keywords)


# --- India matching is word-bounded ------------------------------------------
# Was: a substring check, so "Indianapolis, IN" passed the India-or-remote filter.

@pytest.mark.parametrize("loc", ["Indianapolis, IN", "Indiana, USA", "Indianola"])
def test_us_locations_are_not_india(loc):
    assert is_india_location(loc) is False


@pytest.mark.parametrize("loc", ["Bengaluru, KA", "Remote - India", "Gurugram",
                                 "New Delhi", "Pune, Maharashtra", "INDIA"])
def test_indian_locations_still_match(loc):
    assert is_india_location(loc) is True


# --- remote roles still respect geography when the posting names one ----------
# Was: any remote role skipped the location filter entirely, so a real posting
# reading "fully remote (within the U.S.)" surfaced for an India search.

def _remote(desc, location="San Francisco, CA"):
    j = _job(location=location)
    j.remote, j.description = True, desc
    return j


def test_us_only_remote_is_dropped_for_an_india_search():
    job = _remote("Compensation & Flexibility: $50/hour, and fully remote (within the U.S.)")
    assert passes_filters(job, Filters(locations=["India"])) is False
    assert passes_filters(job, Filters(locations=["United States"])) is True


@pytest.mark.parametrize("desc", [
    "This is a fully remote role.",                      # no region named
    "Remote (anywhere in the world)",                    # explicitly global
    "Remote - India",                                    # matches the search
    "Remote. We have offices in the US and India.",      # both named
])
def test_reachable_remote_roles_are_kept(desc):
    assert passes_filters(_remote(desc), Filters(locations=["India"])) is True


def test_bare_us_pronoun_does_not_read_as_a_country_restriction():
    """`\\bus\\b` would fire on ordinary JD boilerplate and hide valid roles."""
    job = _remote("Fully remote. Come join us and help us build the future!")
    assert remote_scopes(job.description) == set()
    assert passes_filters(job, Filters(locations=["India"])) is True


def test_unmappable_wanted_location_does_not_filter():
    # "Springfield" maps to no region, so we can't judge - stay conservative
    job = _remote("fully remote (within the U.S.)")
    assert passes_filters(job, Filters(locations=["Springfield"])) is True


def test_country_named_far_from_the_word_remote_is_ignored():
    # boilerplate mentioning a country shouldn't be read as the remote scope
    job = _remote("Fully remote position. " + "x" * 400 + " Our investors are based in Canada.")
    assert remote_scopes(job.description) == set()


def test_onsite_location_filtering_is_unchanged():
    onsite = _job(location="Berlin, Germany")
    onsite.remote = False
    assert passes_filters(onsite, Filters(locations=["India"])) is False
    assert passes_filters(_job(location="Bengaluru"), Filters(locations=["India"])) is True


# --- YC output is usable ------------------------------------------------------
# Was: relative hrefs exported as "/jobs/123", and display names handed to the
# ATS sources as board slugs ("Acme Logistics Pvt Ltd" -> a URL with spaces).

YC_HTML = """<html><body>
<div class="job"><a class="job-title" href="/jobs/98765">Operations Intern</a>
<span class="company">Acme Logistics Pvt Ltd</span>
<span class="location">Bengaluru</span><p class="desc">ops</p></div>
</body></html>"""


def test_yc_urls_are_absolute():
    job = YCSource().parse_listing(YC_HTML)[0]
    assert job.url == "https://www.workatastartup.com/jobs/98765"


def test_yc_discovered_slugs_are_slug_shaped():
    src = YCSource()
    src.parse_listing(YC_HTML)
    assert src.discovered_slugs == ["acmelogisticspvtltd"]
    assert src.parse_listing(YC_HTML)[0].company == "Acme Logistics Pvt Ltd"


# --- YC's current card grid parses at all -------------------------------------
# Was: the selectors (div.job / a.job-title / span.company) matched the old
# markup only, so the source silently returned zero jobs on every run.

GRID_FIX = pathlib.Path(__file__).parent / "fixtures" / "yc_jobs_grid.html"


def test_yc_parses_the_current_card_grid():
    src = YCSource()
    jobs = src.parse_listing(GRID_FIX.read_text(encoding="utf-8"))
    assert len(jobs) == 1, "expected only the intern role, not the senior one"
    job = jobs[0]
    assert job.title == "Software Engineering Intern"
    assert job.company == "Seeing Systems"          # batch suffix + nbsp stripped
    assert job.url == "https://www.workatastartup.com/jobs/94623"
    assert job.location.startswith("London, England, GB")
    assert src.discovered_slugs == ["seeingsystems"]


def test_yc_location_skips_employment_type_and_pay_chips():
    from internscout.sources.yc import _pick_location
    assert _pick_location(["Intern", "London, GB", "Full stack", "£2K - £3K GBP"]) == "London, GB"
    assert _pick_location(["Fulltime", "Remote", "Full stack", "$124K - $188K CAD"]) == "Remote"
    assert _pick_location(["Intern", "$50K - $60K"]) == ""


def test_yc_still_parses_the_legacy_markup():
    """The old fixture must keep working; site markup rotates back and forth."""
    legacy = pathlib.Path(__file__).parent / "fixtures" / "yc_jobs.html"
    jobs = YCSource().parse_listing(legacy.read_text(encoding="utf-8"))
    assert len(jobs) == 1
    assert jobs[0].title == "Software Engineer Intern"


def test_slugify_matches_seed_file_convention():
    assert slugify("Razorpay Software Private Limited") == "razorpaysoftwareprivatelimited"
    assert slugify("") == ""


# --- Indeed keeps results on the domain they came from ------------------------

INDEED_HTML = """<html><body><div class="job_seen_beacon">
<span id="jobTitle-1">Supply Chain Intern</span>
<span data-testid="company-name">Foo</span>
<span data-testid="text-location">Pune</span>
<a class="jcs-JobTitle" href="/rc/clk?jk=abc123">x</a></div></body></html>"""


def test_indeed_job_urls_use_the_search_domain():
    job = IndeedSource().parse_results(INDEED_HTML, "in.indeed.com")[0]
    assert job.url.startswith("https://in.indeed.com/")


def test_indeed_defaults_to_the_global_domain():
    assert IndeedSource().parse_results(INDEED_HTML)[0].url.startswith("https://www.indeed.com/")


# --- the results table isn't buried in request logs ---------------------------

def test_scrapling_info_logs_are_filtered_out_by_default():
    """Was: one INFO 'Fetched (200) <GET ...>' line per request buried the table.

    Asserts the filter (not the level) does the work, since scrapling resets its
    own level to INFO whenever it is first imported.
    """
    import logging
    from internscout.cli import _setup_logging

    log = logging.getLogger("scrapling")
    for f in list(log.filters):
        log.removeFilter(f)
    _setup_logging(verbose=False)
    log.setLevel(logging.INFO)          # simulate scrapling importing afterwards

    info = logging.LogRecord("scrapling", logging.INFO, __file__, 1, "Fetched (200)", None, None)
    warn = logging.LogRecord("scrapling", logging.WARNING, __file__, 1, "blocked", None, None)
    # Logger.filter() returns the record (truthy), not True, since 3.12
    assert not log.filter(info), "INFO chatter should be suppressed"
    assert log.filter(warn), "real warnings must still reach the user"
    assert log.propagate is False, "scrapling has its own handler; propagating double-prints"


def test_verbose_lets_scrapling_logs_through():
    import logging
    from internscout.cli import _setup_logging

    log = logging.getLogger("scrapling")
    for f in list(log.filters):
        log.removeFilter(f)
    _setup_logging(verbose=True)
    info = logging.LogRecord("scrapling", logging.INFO, __file__, 1, "Fetched (200)", None, None)
    assert log.filter(info)
    for f in list(log.filters):
        log.removeFilter(f)


# --- LLM ranking can't duplicate or mis-index jobs ----------------------------

def test_llm_rank_ignores_repeated_and_bogus_indices():
    jobs = [_job(title="A", url="a"), _job(title="B", url="b")]
    query = UserQuery(prompt="p", filters=Filters())
    fo = FanOut(search_queries=[], keywords=["intern"], domain_tags=[])
    def fake_llm(system, user):
        return ('[{"i":0,"score":90,"reason":"x"},{"i":0,"score":80,"reason":"dup"},'
                '{"i":99,"score":70,"reason":"oob"},{"i":true,"score":60,"reason":"bool"},'
                '{"i":1,"score":"bad","reason":"unparseable score"}]')
    ranked = _llm_rank(jobs, query, fo, load_config(), fake_llm)
    assert [r.job.title for r in ranked] == ["A", "B"]
    assert ranked[1].score == 0.0
