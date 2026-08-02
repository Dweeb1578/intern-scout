"""India-location recognition for the default geography filter.

Scraped job locations rarely contain the literal word "India" - they read
"Bengaluru, KA", "Gurgaon", "Remote - India", etc. So matching the country
means matching its major cities and regions too.
"""

import re

# Lowercased hints. Kept to unambiguous city/region names + the country itself
# to avoid false positives (e.g. 2-letter codes like "in" would over-match).
INDIA_HINTS = {
    "india", "bharat",
    "bengaluru", "bangalore", "mumbai", "bombay", "delhi", "new delhi",
    "gurgaon", "gurugram", "noida", "hyderabad", "pune", "chennai", "madras",
    "kolkata", "calcutta", "ahmedabad", "jaipur", "chandigarh", "kochi",
    "cochin", "coimbatore", "indore", "nagpur", "trivandrum",
    "thiruvananthapuram", "mysuru", "mysore", "vadodara", "surat",
    "visakhapatnam", "vizag", "bhubaneswar", "lucknow", "kanpur", "bhopal",
}

# Matched on word boundaries, not as bare substrings: a plain `"india" in text`
# check also fires on "Indianapolis, IN" and "Indiana, USA", quietly letting US
# roles through the India-or-remote filter.
_INDIA_RE = re.compile(
    r"\b(?:%s)\b" % "|".join(re.escape(h) for h in sorted(INDIA_HINTS, key=len, reverse=True))
)

def is_india_location(text: str) -> bool:
    """True if the location string looks like it's in India."""
    return bool(_INDIA_RE.search((text or "").lower()))


# --- remote-role hiring geography --------------------------------------------
# "Remote" rarely means "remote from anywhere": most postings are remote *within
# a country*. Treating every remote role as location-free surfaces things like
# "fully remote (within the U.S.)" for someone searching India.

# Coarse region tokens. Deliberately narrow patterns - a bare `\bus\b` would fire
# on "join us" / "contact us" in any job description, so US only matches when it
# is punctuated or qualified.
_SCOPE_PATTERNS = (
    ("india", r"\b(?:india|bharat)\b"),
    ("us", r"(?:\bu\.s\.a?\.?|\busa\b|\bunited states\b|\bus[-\s](?:based|only|remote)\b"
            r"|\b(?:within|in|across)\s+the\s+us\b)"),
    ("uk", r"\b(?:u\.k\.|uk|united kingdom|england|scotland|wales)\b"),
    ("canada", r"\b(?:canada|canadian)\b"),
    ("eu", r"\b(?:eu|emea|europe|european union|eea)\b"),
    ("australia", r"\b(?:australia|australian|anz)\b"),
    ("singapore", r"\bsingapore\b"),
)
_SCOPE_RES = tuple((token, re.compile(rx, re.I)) for token, rx in _SCOPE_PATTERNS)

# An explicit "anywhere" beats any country mentioned nearby.
_ANYWHERE_RE = re.compile(
    r"\b(?:anywhere|worldwide|world[-\s]?wide|globally|global remote|any (?:time ?zone|country))\b",
    re.I)

# Only text near the word "remote" counts. A JD can name a dozen countries in its
# boilerplate; the restriction is the one attached to the remote arrangement.
_REMOTE_WINDOW_RE = re.compile(r".{0,40}\bremote\b.{0,70}", re.I | re.S)


def remote_scopes(text: str) -> set[str]:
    """Regions a remote role appears to be restricted to.

    Empty set means "no restriction found", which is treated as unrestricted -
    the conservative reading, so an unrecognized phrasing keeps the role visible
    instead of silently dropping it.
    """
    found: set[str] = set()
    for window in _REMOTE_WINDOW_RE.findall(text or ""):
        if _ANYWHERE_RE.search(window):
            return set()
        for token, rx in _SCOPE_RES:
            if rx.search(window):
                found.add(token)
    return found


def location_scope(wanted: str) -> str | None:
    """Map a user's wanted location onto a region token, or None if unmappable."""
    w = (wanted or "").strip()
    if not w:
        return None
    if is_india_location(w):
        return "india"
    for token, rx in _SCOPE_RES:
        if rx.search(w):
            return token
    return None
