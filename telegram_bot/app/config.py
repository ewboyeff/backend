import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    bot_token: str
    channel_id: str
    database_url: str
    admin_ids: list[int]

def load_config() -> Config:
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip().isdigit()]

    return Config(
        bot_token=os.getenv("BOT_TOKEN", ""),
        channel_id=os.getenv("CHANNEL_ID", ""),
        database_url=os.getenv("DATABASE_URL", ""),
        admin_ids=admin_ids,
    )

config = load_config()
