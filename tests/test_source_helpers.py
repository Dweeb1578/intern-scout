from internscout.models import Job
from internscout.sources.base import is_intern_role, detect_remote, dedupe

def test_is_intern_role():
    assert is_intern_role("Software Engineering Intern")
    assert is_intern_role("New Grad Engineer")
    assert is_intern_role("Backend Co-op")
    assert not is_intern_role("Senior Staff Engineer")

def test_is_intern_role_business_early_career():
    # India business early-career titles should count as intern-equivalent roles
    assert is_intern_role("Management Trainee")
    assert is_intern_role("Supply Chain Trainee")
    assert is_intern_role("Graduate Programme - Operations")
    assert is_intern_role("Operations Intern")
    assert not is_intern_role("VP of Operations")

def test_detect_remote():
    assert detect_remote("This is a Remote position") is True
    assert detect_remote("On-site in NYC") is False
    assert detect_remote("Great team") is None

def test_dedupe():
    j1 = Job("t","c","l",None,"http://x/1","d","s")
    j2 = Job("t","c","l",None,"http://x/1","d2","s")
    j3 = Job("t","c","l",None,"http://x/2","d","s")
    assert len(dedupe([j1, j2, j3])) == 2
