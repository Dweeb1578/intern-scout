from dataclasses import dataclass
import json
import re
from .config import Config, has_llm

_STOP = {"a","an","at","the","for","in","of","to","and","or","with","intern",
         "internship","want","looking","role","position","i","my","me","as"}

_SYNONYMS = {
    # tech
    "backend": ["api", "server", "django", "fastapi", "node"],
    "frontend": ["react", "ui", "javascript", "typescript"],
    "ml": ["machine learning", "pytorch", "model", "ai"],
    "data": ["analytics", "sql", "pipeline"],
    "design": ["figma", "ux", "ui"],
    # operations
    "operations": ["ops", "operations", "process", "fulfillment", "city operations",
                   "business operations", "operations analyst", "logistics"],
    "ops": ["operations", "process", "fulfillment", "business operations"],
    # go-to-market (GTM)
    "gtm": ["go-to-market", "sales", "marketing", "growth", "business development",
            "revenue", "partnerships", "demand generation", "revops"],
    "sales": ["business development", "bd", "inside sales", "account executive",
              "sdr", "revenue", "go-to-market"],
    "marketing": ["growth", "brand", "demand generation", "content", "performance marketing"],
    "growth": ["marketing", "demand generation", "user acquisition", "gtm"],
    # supply chain
    "supply": ["supply chain", "procurement", "sourcing", "inventory", "logistics",
               "warehouse", "demand planning", "vendor", "fulfillment"],
    "chain": ["supply chain", "procurement", "logistics", "inventory"],
    "procurement": ["sourcing", "vendor", "supply chain", "purchasing"],
    "logistics": ["supply chain", "fulfillment", "warehouse", "last mile", "operations"],
    # management / strategy
    "management": ["management trainee", "program management", "project management",
                   "chief of staff", "founder's office", "business analyst"],
    "strategy": ["strategy and operations", "chief of staff", "founder's office",
                 "business analyst", "consulting", "program management"],
    "consulting": ["strategy", "business analyst", "advisory"],
    "business": ["business analyst", "business development", "business operations",
                 "strategy", "operations"],
    "finance": ["fp&a", "financial analyst", "accounting", "treasury"],
    "product": ["product management", "associate product manager", "apm"],
}

@dataclass
class FanOut:
    search_queries: list[str]
    keywords: list[str]
    domain_tags: list[str]

def _clean_str_list(value) -> list[str]:
    """Coerce a field of model-generated JSON into a de-duped list of strings.

    The model is asked for lists of strings but is not bound to deliver them: a
    bare string, a nested list, or numbers ("2026") all show up in practice.
    Downstream code calls .lower() on these, so anything non-string that slips
    through crashes the whole run rather than degrading it.
    """
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    out = []
    for v in value:
        s = v.strip() if isinstance(v, str) else (str(v).strip() if isinstance(v, (int, float)) else "")
        if s and s not in out:
            out.append(s)
    return out

def _fallback_fanout(prompt: str) -> FanOut:
    tokens = [t for t in re.findall(r"[a-zA-Z+#]+", prompt.lower()) if t not in _STOP and len(t) > 1]
    keywords = list(dict.fromkeys(tokens))
    for t in list(keywords):
        keywords.extend(_SYNONYMS.get(t, []))
    keywords = list(dict.fromkeys(keywords))
    base = " ".join(tokens[:3]) or "intern"
    queries = list(dict.fromkeys([
        f"{base} intern",
        f"{base} internship",
        f"{tokens[0] if tokens else 'software'} intern",
    ]))
    return FanOut(search_queries=queries, keywords=keywords, domain_tags=tokens[:2])

_SYSTEM = (
    "You expand a job-seeker's free-text internship prompt into search inputs. "
    "Return ONLY JSON with keys: search_queries (4-8 short job-search phrasings), "
    "keywords (skills/terms incl. synonyms), domain_tags (1-3 coarse domains)."
)

def fan_out(prompt: str, cfg: Config, llm=None) -> FanOut:
    if llm is None and not has_llm(cfg):
        return _fallback_fanout(prompt)
    if llm is None:
        llm = _make_groq_caller(cfg)
    try:
        raw = llm(_SYSTEM, prompt)
        data = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
        if not isinstance(data, dict):
            return _fallback_fanout(prompt)
        queries = _clean_str_list(data.get("search_queries"))
        if queries:
            return FanOut(
                search_queries=queries,
                keywords=_clean_str_list(data.get("keywords")),
                domain_tags=_clean_str_list(data.get("domain_tags")),
            )
        return _fallback_fanout(prompt)
    except Exception:
        return _fallback_fanout(prompt)

def _make_groq_caller(cfg: Config):
    from groq import Groq
    client = Groq(api_key=cfg.groq_api_key)
    def call(system: str, user: str) -> str:
        resp = client.chat.completions.create(
            model=cfg.groq_model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.3,
        )
        return resp.choices[0].message.content
    return call
