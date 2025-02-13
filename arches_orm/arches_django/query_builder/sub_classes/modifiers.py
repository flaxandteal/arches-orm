class QueryBuilderModifier:
    _instance_query_builder = None;
    _wrapper_instance = None;
    _queryset_tiles = None;

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;
    
    def order_by(self):
        return self._instance_query_builder