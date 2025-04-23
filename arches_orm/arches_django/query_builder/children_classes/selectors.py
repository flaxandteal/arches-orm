from arches.app.models.models import TileModel
from arches_orm.arches_django.query_builder.utilities import transform_filter_structure_towards_query, transform_exclude_structure_towards_query
from typing import Dict, List, TYPE_CHECKING, TypedDict
from django.db.models import ExpressionWrapper, QuerySet
from arches_orm.arches_django.query_builder.annotations.annotations import annotation_resource_merge_tile_data
from django.db.models import Case, When, Value, IntegerField

from django.contrib.postgres.fields import JSONField as PostgreSQLJSONField
from django.db.models.expressions import RawSQL

from arches_orm.arches_django.query_builder.config import RESOURCE_MERGED_TILE_DATA_KEY

if TYPE_CHECKING:
    from arches_orm.arches_django.query_builder.query_builder import FilterStructure, ExcludeStructure

class QuerysetOffset(TypedDict):
    offset: int | None
    limit: int | None

class QueryBuilderSelectors:
    _instance_query_builder = None;
    _wrapper_instance = None;
    _resourceinstances_ids = []

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;
    
    def _default_get_tiles(
            self, 
            annotations: Dict[str, ExpressionWrapper] | None = None,
            filter_structures: List["FilterStructure"] | None = None,
            exclude_structures: List["ExcludeStructure"] | None = None,
            order_by: List[str] | None = None,
            offset: QuerysetOffset = None
        ) -> QuerySet[TileModel]:
        """
        This method is to handle building the query builder, towards the query_builder.py method "create_wkri_with_datatype_values", 

        Args:
            annotations (Dict[str, ExpressionWrapper] | None, optional): The annotations which are set towards the data JSON, remember
                that the tile data is stored within a JSON_B column, therefore we need annotations to fix out the value with the
                node alias. Defaults to None.
            filter_structures (List[&quot;FilterStructure&quot;] | None, optional): This structure is mainly used for the .filter()
                towards Django and we transform this filter_structures to acceptable Q. Defaults to None.
            exclude_structures (List[&quot;ExcludeStructure&quot;] | None, optional): This structure is mainly used for the .exclude()
                towards Django and we transform this exclude_structures to acceptable Q. Defaults to None.
            order_by (List[str] | None, optional): This structure is used towards .order_by() in django. Defaults to None.
            offset (QuerysetOffset, optional): This is towards getting a range of records, therefore we can use [50:23]. Defaults to None.

        Return:
            QuerySet[TileModel]: The tiles which are returned
        """

        def _callback_get_tiles(**defaultFilterTileAgrs):
            # class JsonbObjectAggFromLateral(Func):
            #     function = 'jsonb_object_agg'
            #     output_field = JSONField()
            #     template = """
            #     (SELECT jsonb_object_agg(kv.key, kv.value)
            #     FROM jsonb_each(%(expressions)s) AS kv
            #     )"""

            # testTiles = TileModel.objects.filter(
            #     resourceinstance_id='bb6cffff-9947-443d-9a82-16b35a417213'
            # ).annotate(
            #     merged_tiledata=JsonbObjectAggFromLateral('data')
            # ).values('resourceinstance_id', 'merged_tiledata')
                
            # testTiles = TileModel.objects.values('resourceinstance_id').annotate(
            #     resource_merged_tile_data=RawSQL(
            #         """
            #         (
            #             SELECT jsonb_object_agg(kv.key, kv.value)
            #             FROM tiles AS t
            #             JOIN jsonb_each(t.tiledata) AS kv ON true
            #             WHERE t.resourceinstanceid = tiles.resourceinstanceid
            #         )
            #         """, 
            #         [],
            #         output_field=PostgreSQLJSONField()  # This is the key fix
            #     )
            # ).distinct().annotate(**annotations)

            # print(testTiles)

            # print('WORKS?', testTiles.filter(resourceinstance_id="bb6cffff-9947-443d-9a82-16b35a417213"))


            queryset_tiles = TileModel.objects.values('resourceinstance_id')
            self._resourceinstances_ids = []

            def _apply_annotations():
                nonlocal queryset_tiles

                queryset_tiles = queryset_tiles.annotate(
                    **{RESOURCE_MERGED_TILE_DATA_KEY: annotation_resource_merge_tile_data(self._instance_query_builder._database_engine)}
                ).distinct().annotate(
                    **self._instance_query_builder._before_annotations
                ).annotate(
                    **annotations
                )

            def _get_valid_resource_instance_ids():
                nonlocal queryset_tiles
                _apply_annotations()

                if (filter_structures):
                    queryset_tiles = queryset_tiles.filter(
                        transform_filter_structure_towards_query(filter_structures), 
                        **defaultFilterTileAgrs
                    )
                    print('filter_structures : ', queryset_tiles)

                else:
                    queryset_tiles = queryset_tiles.filter(**defaultFilterTileAgrs)

                if (exclude_structures):
                    # * When you use .annotate(), the annotated fields exist only within that specific query chain. 
                    # * This means that if you need to use an annotation in both .filter() and .exclude(), you might have to reapply the annotation 
                    # * before using .exclude().
                    _apply_annotations()
                  
                    queryset_tiles = queryset_tiles.exclude(
                        transform_exclude_structure_towards_query(exclude_structures)
                    )

                if (order_by):
                    _apply_annotations()
                    queryset_tiles = queryset_tiles.order_by(*order_by)

                if offset and (offset['limit'] is not None or offset['offset'] is not None):
                    limit_value = offset.get('limit')
                    offset_value = offset.get('offset', 0) or 0

                    if limit_value is not None:
                        return list(queryset_tiles.values_list('resourceinstance_id', flat=True)[offset_value:offset_value + limit_value])
                    else:
                        return list(queryset_tiles.values_list('resourceinstance_id', flat=True)[offset_value:])
                    
                else:
                    return list(queryset_tiles.values_list('resourceinstance_id', flat=True))
                
            self._resourceinstances_ids = _get_valid_resource_instance_ids() # ? We put this in a global variable for count()

            return TileModel.objects.filter(resourceinstance_id__in=self._resourceinstances_ids).order_by(
                Case(*[When(resourceinstance_id=pk, then=Value(index)) for index, pk in enumerate(self._resourceinstances_ids)], output_field=IntegerField())
            )
            
        return _callback_get_tiles

    def _default_handle_selector_return(self, callback_get_tiles) -> List[type]:
        """
        Method handles the return towards the selectors below. The purpose is to keep all the handling for the return the same, incase something in the 
        selectors needed changed

        Args:
            callback_get_tiles (() => List[WKRI]): Callback method should return a list of WKRIs

        Returns:
            List[WKRI]: This is the list of WKRI's
        """
        lazy_mode = self._instance_query_builder._lazy_mode;

        results = self._instance_query_builder.create_wkri_with_datatype_values(
            callback_get_tiles=callback_get_tiles,
            lazy_mode=lazy_mode
        )
    
        return results

    def get(self) -> List[type]:
        """
        Method gets resource, the purpose is this method is the default for getting records towards filtering & modification, etc.

        Returns:
            List[WKRI]: This is the list of WKRI's
        """
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
        
        return self._default_handle_selector_return(callback_get_tiles=callback_get_tiles)
    
    def count(self) -> List[type]:
        """
        Method returns the count of the resources within the model, we can filter and exclude this
        
        Returns:
            List[WKRI]: This is the list of WKRI's
        """
        annotations = self._instance_query_builder._annotations;
        filter_structures = self._instance_query_builder._filter_structures;
        exclude_structures = self._instance_query_builder._exclude_structures;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            filter_structures=filter_structures,
            exclude_structures=exclude_structures,
        )

        permittedNodegroupIds: List[str | None] = self._wrapper_instance._permitted_nodegroups()
        defaultFilterTileAgrs: Dict[str, any] = {
            'nodegroup_id__in': permittedNodegroupIds
        }

        callback_get_tiles(**defaultFilterTileAgrs)

        return len(self._resourceinstances_ids)

    
    def offset(self, offset: None | int = None, limit: None | int = None) -> List[type]:
        """
        This method handles getting a range of resources for example offset is 4 and the limit is 20

        Args:
            offset (None | int, optional): The offset within the tiles table. Defaults to None.
            limit (None | int, optional): The limit of resources gained. Defaults to None.

        Returns:
            List[WKRI]: This is the list of WKRI's
        """
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
        
        return self._default_handle_selector_return(callback_get_tiles=callback_get_tiles)

    
    def first(self) -> type:
        """
        Method handles getting the first resource from the query. You can see I add limit: 1 which creates a SQL query to only get the first record

        Returns:
            WKRI: This is a single resource instance (Well Known Resource Instance)
        """
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
        
        return self._default_handle_selector_return(callback_get_tiles)[0]



    def all(self) -> List[type]:
        """
        Method grabs all resources, completely ignoring filtering section options and preforming 

        Returns:
            List[WKRI]: This is the list of WKRI's
        """
        annotations = self._instance_query_builder._annotations;
        order_by = self._instance_query_builder._order_by;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            order_by=order_by
        )
        
        return self._default_handle_selector_return(callback_get_tiles)

    
    def find(self, resourceinstance_id: str) -> type:
        """
        Method finds a resource based on the resource instance id 

        Args:
            resourceinstance_id (str): The is the resource instance id

        Returns:
            WKRI: This is a single resource instance (Well Known Resource Instance)
        """
        annotations = self._instance_query_builder._annotations;
        order_by = self._instance_query_builder._order_by;

        callback_get_tiles = self._default_get_tiles(
            annotations=annotations,
            order_by=order_by,
            offset={ 'limit': 1 },
            filter_structures=[
                {
                    'logical_operator': 'AND',
                    'conditions': {
                        'resourceinstance_id': resourceinstance_id
                    }
                }
            ]
        )

        return self._default_handle_selector_return(callback_get_tiles)[0]
        
        