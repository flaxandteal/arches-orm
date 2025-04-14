from .adapter import StaticAdapter
from arches_orm.adapter import get_adapter

adapter = get_adapter(StaticAdapter.key)

__all__ = ["adapter"]
