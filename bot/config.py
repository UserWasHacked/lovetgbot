import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class PackConfig:
    generations: int
    stars: int
    payload: str


@dataclass(frozen=True)
class Config:
    bot_token: str
    gemini_api_key: str
    gemini_model: str
    database_path: Path
    free_generations: int
    pack_5: PackConfig
    pack_20: PackConfig


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is required")

    db_path = os.getenv("DATABASE_PATH", "data/bot.db").strip()
    database_path = Path(db_path)
    if not database_path.is_absolute():
        database_path = BASE_DIR / database_path

    return Config(
        bot_token=bot_token,
        gemini_api_key=gemini_api_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip(),
        database_path=database_path,
        free_generations=int(os.getenv("FREE_GENERATIONS", "2")),
        pack_5=PackConfig(
            generations=5,
            stars=int(os.getenv("PACK_5_STARS", "50")),
            payload="pack_5",
        ),
        pack_20=PackConfig(
            generations=20,
            stars=int(os.getenv("PACK_20_STARS", "150")),
            payload="pack_20",
        ),
    )
