from datetime import datetime, timezone
from uuid import uuid4


def make_reference(prefix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}-{uuid4().hex[:6].upper()}"

