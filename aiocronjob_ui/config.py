import dataclasses
import os


@dataclasses.dataclass
class Settings:
    api_url: str = os.getenv("API_URL", "http://localhost:8000/api")
