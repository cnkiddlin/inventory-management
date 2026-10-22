from datetime import datetime

from pydantic import BaseModel


class HealthRead(BaseModel):
    status: str
    database: str
    version: str
    timestamp: datetime

