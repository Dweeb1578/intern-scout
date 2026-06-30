from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    groq_api_key: str | None
    groq_model: str
    seed_path: Path
    per_source_timeout: int
    matcher_mode: str

def load_config() -> Config:
    key = os.getenv("GROQ_API_KEY") or None
    return Config(
        groq_api_key=key,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        seed_path=Path(__file__).parent / "data" / "seed_companies.json",
        per_source_timeout=int(os.getenv("INTERNSCOUT_TIMEOUT", "30")),
        matcher_mode=os.getenv("INTERNSCOUT_MATCHER", "hybrid"),
    )

def has_llm(cfg: Config) -> bool:
    return bool(cfg.groq_api_key)
