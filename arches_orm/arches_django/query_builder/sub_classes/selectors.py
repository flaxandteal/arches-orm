from arches.app.models.models import TileModel

class QueryBuilderSelectors:
    _instance_query_builder = None;
    _wrapper_instance = None;
    _queryset_tiles = None;

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;
    
    @property
    def queryset_tiles(self):
        if not self._queryset_tiles:
            self._queryset_tiles = TileModel.objects;

        return self._queryset_tiles;

    @queryset_tiles.setter
    def queryset_tiles(self, value):
        self._queryset_tiles = value;

    def get(self):
        annotations = self._instance_query_builder._annotations;
        filters = self._instance_query_builder._filters;
 
        def callable_get_tiles(**defaultFilterTileAgrs):
            self.queryset_tiles = self.queryset_tiles.annotate(**annotations)
            self.queryset_tiles = self.queryset_tiles.filter(**filters, **defaultFilterTileAgrs)
            return self.queryset_tiles.select_related('resourceinstance', 'nodegroup').iterator()

        return self._instance_query_builder.create_wkri_with_datatype_values(callable_get_tiles=callable_get_tiles)