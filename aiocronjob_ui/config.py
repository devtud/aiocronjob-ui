import dataclasses
import os
import logging


@dataclasses.dataclass
class Settings:
    api_url: str = os.getenv("API_URL", "http://localhost:8000/api")


logger = logging.getLogger("aiocronjob-ui")
logger.setLevel(logging.DEBUG)

