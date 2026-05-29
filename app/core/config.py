from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = ""


def get_config() -> Config:
    return Config()
