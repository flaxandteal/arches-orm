from arches.app.models.models import TileModel
from arches_orm.arches_django.query_builder.utilities import transform_filter_structure_towards_query
from typing import Dict, List, TYPE_CHECKING
from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField

if TYPE_CHECKING:
    from arches_orm.arches_django.query_builder.query_builder import FilterStructure

class QueryBuilderSelectors:
    _instance_query_builder = None;
    _wrapper_instance = None;
    _queryset_tiles = None;

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;
    
    @property
    def queryset_tiles(self):
        """
        Method is for getting the tiles model so its defined in 1 place
        """
        if not self._queryset_tiles:
            self._queryset_tiles = TileModel.objects;

        return self._queryset_tiles;

    @queryset_tiles.setter
    def queryset_tiles(self, value):
        """
        Method sets the quertset_tiles
        """
        self._queryset_tiles = value;
    
    def _default_get_tiles(
            self, 
            annotations: Dict[str, ExpressionWrapper] | None = None,
            filter_structures: List["FilterStructure"] | None = None,
            order_by: List[str] | None = None
        ):

        def _callback_get_tiles(**defaultFilterTileAgrs):
            if (annotations):
                self.queryset_tiles = self.queryset_tiles.annotate(**annotations)

            if (filter_structures):
                self.queryset_tiles = self.queryset_tiles.filter(
                    transform_filter_structure_towards_query(filter_structures), 
                    **defaultFilterTileAgrs
                )

            else:
                self.queryset_tiles = self.queryset_tiles.filter(**defaultFilterTileAgrs)

            if (order_by):
                self.queryset_tiles = self.queryset_tiles.order_by(*order_by)  

            return self.queryset_tiles.select_related('resourceinstance', 'nodegroup').iterator()
        
        return _callback_get_tiles

    def get(self):
        annotations = self._instance_query_builder._annotations;
        filter_structures = self._instance_query_builder._filter_structures;
        order_by = self._instance_query_builder._order_by;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            filter_structures=filter_structures,
            order_by=order_by
        )
        
        return self._instance_query_builder.create_wkri_with_datatype_values(
            callback_get_tiles=callback_get_tiles
        )
    
    def all(self):
        annotations = self._instance_query_builder._annotations;
        order_by = self._instance_query_builder._order_by;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            order_by=order_by
        )
        
        return self._instance_query_builder.create_wkri_with_datatype_values(
            callback_get_tiles=callback_get_tiles
        )