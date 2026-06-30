from dataclasses import dataclass, field

@dataclass
class Filters:
    remote: str = "any"            # "remote" | "onsite" | "any"
    locations: list[str] = field(default_factory=list)
    grad_year: int | None = None
    max_results: int = 25

@dataclass
class UserQuery:
    prompt: str
    filters: Filters

@dataclass
class Job:
    title: str
    company: str
    location: str
    remote: bool | None
    url: str
    description: str
    source: str
    posted_at: str | None = None

    @property
    def dedupe_key(self) -> str:
        if self.url:
            return self.url.strip().lower()
        return f"{self.title.strip().lower()}|{self.company.strip().lower()}"

@dataclass
class RankedJob:
    job: Job
    score: float
    reason: str
