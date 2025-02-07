import re
from ..utilities import transform_query
from django.db.models import Func, F, ExpressionWrapper, IntegerField, CharField
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge, TileModel
from .annotations import annotation_string_datatype

class QueryBuilderFilters:
    _instance_query_builder = None;
    _wrapper_instance = None;


    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;

    def _where_handle_datatype_string():
        print('HERE!')


    allowed_operators_datatypes = {
        'where': {
            '=': {
                'string': _where_handle_datatype_string
            }
        }
    }

    def where(self, *args):     

        filters = [];
        annotations = {};

        for index in range(len(args)):
        
            query = transform_query(args[index])

            node = self._wrapper_instance._node_objects_by_alias().get(query['key'])

            # ! LAST LEFT OFF
            if (node.datatype == 'string'):
                annotations.append(annotation_string_datatype(node.nodeid))

                continue; 

            print(node.nodeid)
            print(node.datatype)
            print('HERE')

            # edges_range_to_domain = self._instance_query_builder.edges_range_to_domain

            # Create dynamic annotations
            annotations = {}

            # Adding 7 dynamic annotations for 'ages' field in 'data'
            # for i in range(1, 8):
            #     annotations[f'dynamic_value_{i}'] = ExpressionWrapper(
            #         F(f'data__5f8ded26-7ef9-11ea-8e29-f875a44e0e11__en__value'),  # Set logic here, for example, the 'ages' in English
            #         output_field=CharField()
            #     )

            
            queryset = queryset.filter(dynamic_value_1='TEST')

        queryset = TileModel.objects.annotate(**annotations)
        queryset = queryset.filter(**filters)
        print(queryset)

    def where_in():
        return;

    