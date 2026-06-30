"""India-location recognition for the default geography filter.

Scraped job locations rarely contain the literal word "India" - they read
"Bengaluru, KA", "Gurgaon", "Remote - India", etc. So matching the country
means matching its major cities and regions too.
"""

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

def is_india_location(text: str) -> bool:
    """True if the location string looks like it's in India."""
    t = (text or "").lower()
    return any(h in t for h in INDIA_HINTS)
