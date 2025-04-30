
from typing import List, TYPE_CHECKING

class QueryBuilderCombinator:
    _instance_query_builder = None;
    _wrapper_instance = None;
    _queryset_tiles = None;

    if TYPE_CHECKING:
        from arches_orm.arches_django.query_builder.query_builder import QueryBuilder

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;
    
    def join(self, **kwargs):
        self._instance_query_builder._joins = kwargs;
        self._instance_query_builder._joins_keys = kwargs.keys();
