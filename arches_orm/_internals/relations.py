import uuid
from typing import Protocol


class WKRI(Protocol):
    graph_id: uuid.UUID
    _cross_record: dict | None = None
