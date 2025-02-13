import re
from ..utilities import transform_query, annotation_key
from django.db.models import Func, F, ExpressionWrapper, IntegerField, CharField
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge, TileModel
import uuid

class QueryBuilderFilters:
    _instance_query_builder = None;
    _wrapper_instance = None;

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;

    # allowed_operators_datatypes = {
    #     'where': {
    #         '=': {
    #             'string': _where_handle_datatype_string
    #         }
    #     }
    # }

    def where(self, *args):     
        nodes = self._wrapper_instance._node_objects_by_alias();

        for index in range(len(args)):
            query = transform_query(args[index])
            node_alias = query['key'];
            node = nodes.get(node_alias)

            self._instance_query_builder.set_annotation(
                node_alias, 
                node
            )

            if (query['operator'] == '='):
                self._instance_query_builder._filters[annotation_key(node_alias)] = query['value']
    
        return self._instance_query_builder

    def where_in():
        return;

    