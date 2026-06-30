import argparse
from internscout.cli import build_query

def _ns(**kw):
    base = dict(prompt="backend intern", remote="any", locations="SF, NYC",
                grad_year=None, limit=20)
    base.update(kw); return argparse.Namespace(**base)

def test_build_query_splits_locations():
    q = build_query(_ns())
    assert q.prompt == "backend intern"
    assert q.filters.locations == ["SF", "NYC"]
    assert q.filters.max_results == 20

def test_build_query_remote_flag():
    q = build_query(_ns(remote="remote", locations=""))
    assert q.filters.remote == "remote"
    # no locations given -> default geography is India (remote roles also pass)
    assert q.filters.locations == ["India"]

def test_build_query_defaults_to_india_when_blank():
    q = build_query(_ns(locations=""))
    assert q.filters.locations == ["India"]
