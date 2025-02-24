from arches.app.models.models import TileModel
from arches_orm.arches_django.query_builder.utilities import transform_filter_exclude_structure_towards_query
from typing import Dict, List, TYPE_CHECKING, TypedDict
from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField

if TYPE_CHECKING:
    from arches_orm.arches_django.query_builder.query_builder import FilterStructure, ExcludeStructure

class QuerysetOffset(TypedDict):
    offset: int | None
    limit: int | None

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
            exclude_structures: List["ExcludeStructure"] | None = None,
            order_by: List[str] | None = None,
            offset: QuerysetOffset = None
        ):


        def _callback_get_tiles(**defaultFilterTileAgrs):
            def _apply_annotations():
                if (annotations):
                    self.queryset_tiles = self.queryset_tiles.annotate(**annotations)

            if (filter_structures):
                _apply_annotations()
                self.queryset_tiles = self.queryset_tiles.filter(
                    transform_filter_exclude_structure_towards_query(filter_structures), 
                    **defaultFilterTileAgrs
                )

            else:
                self.queryset_tiles = self.queryset_tiles.filter(**defaultFilterTileAgrs)

            if (exclude_structures):
                # * When you use .annotate(), the annotated fields exist only within that specific query chain. 
                # * This means that if you need to use an annotation in both .filter() and .exclude(), you might have to reapply the annotation 
                # * before using .exclude().
                _apply_annotations()
                self.queryset_tiles = self.queryset_tiles.exclude(
                    transform_filter_exclude_structure_towards_query(exclude_structures)
                )

            if (order_by):
                self.queryset_tiles = self.queryset_tiles.order_by(*order_by) 

            if offset and (offset['limit'] is not None or offset['offset'] is not None):
                limit_value = offset.get('limit')
                offset_value = offset.get('offset', 0) or 0

                if limit_value is not None:
                    return self.queryset_tiles.select_related('resourceinstance', 'nodegroup')[offset_value:offset_value + limit_value]
                else:
                    return self.queryset_tiles.select_related('resourceinstance', 'nodegroup')[offset_value:]
                
            else:
                return self.queryset_tiles.select_related('resourceinstance', 'nodegroup').iterator()        
        return _callback_get_tiles

    def get(self):
        annotations = self._instance_query_builder._annotations;
        filter_structures = self._instance_query_builder._filter_structures;
        exclude_structures = self._instance_query_builder._exclude_structures;
        order_by = self._instance_query_builder._order_by;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            filter_structures=filter_structures,
            exclude_structures=exclude_structures,
            order_by=order_by
        )
        
        results = self._instance_query_builder.create_wkri_with_datatype_values(
            callback_get_tiles=callback_get_tiles
        )

        return results
    
    def offset(self, offset: None | int = None, limit: None | int = None):
        annotations = self._instance_query_builder._annotations;
        filter_structures = self._instance_query_builder._filter_structures;
        exclude_structures = self._instance_query_builder._exclude_structures;
        order_by = self._instance_query_builder._order_by;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            filter_structures=filter_structures,
            exclude_structures=exclude_structures,
            order_by=order_by,
            offset={ 'limit': limit, 'offset': offset }
        )
        
        results = self._instance_query_builder.create_wkri_with_datatype_values(
            callback_get_tiles=callback_get_tiles
        )

        return results
    
    def first(self):
        annotations = self._instance_query_builder._annotations;
        filter_structures = self._instance_query_builder._filter_structures;
        exclude_structures = self._instance_query_builder._exclude_structures;
        order_by = self._instance_query_builder._order_by;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            filter_structures=filter_structures,
            exclude_structures=exclude_structures,
            order_by=order_by,
            offset={ 'limit': 1 }
        )
        
        results = self._instance_query_builder.create_wkri_with_datatype_values(
            callback_get_tiles=callback_get_tiles
        )

        return results


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
    
    def find(self, resourceinstance_id):
        annotations = self._instance_query_builder._annotations;
        order_by = self._instance_query_builder._order_by;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            order_by=order_by
        )
        
        return self._instance_query_builder.create_wkri_with_datatype_values(
            callback_get_tiles=callback_get_tiles
        )