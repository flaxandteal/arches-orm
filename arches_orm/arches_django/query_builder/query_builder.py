from typing import Iterator, Dict, List, TypedDict, Any, Callable, Optional
from arches.app.models.models import TileModel
from django.core.paginator import Paginator, Page
from arches.app.models.resource import Resource
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge, TileModel
from functools import lru_cache
from arches_orm.arches_django.wrapper import ValueList

from .sub_classes.filters import QueryBuilderFilters
from .sub_classes.selectors import QueryBuilderSelectors
from .sub_classes.modifiers import QueryBuilderModifier

from collections import defaultdict

class WKRIEntry(TypedDict):
    values: Dict[str, Any]
    wkri: type 

LOAD_ALL_NODES = True

class QueryBuilder:
    _instance = None
    _parent_wrapper_instance = None;

    _instance_filters = None;
    _instance_selectors = None;
    _instance_modifiers = None;
    _current_build_stage = None;

    _edges_domain_to_range = None;
    _edges_range_to_domain = None;

    _filters = {};
    _annotations = {};
    _order_by = [];

    def __init__(self, parent_wrapper_instance):
        self._parent_wrapper_instance = parent_wrapper_instance;
        self._instance = self;

        self._instance_filters  = QueryBuilderFilters(self._instance)
        self._instance_modifiers  = QueryBuilderModifier(self._instance)
        self._instance_selectors = QueryBuilderSelectors(self._instance)

    # def _globally_expose_query_builder_additional_methods(instance):
    #     for method_name in dir(instance):
    #         if not method_name.startswith("_") and callable(getattr(instance, method_name)):
    #             setattr(instance, method_name, getattr(instance, method_name))

    def __getattr__(self, name):
        if not self._current_build_stage and hasattr(self._instance_filters, name):
            self._current_build_stage = 'filters'
            return getattr(self._instance_filters, name)

        elif (self._current_build_stage == 'filters' or self._current_build_stage == None) and hasattr(self._instance_modifiers, name):
            self._current_build_stage = 'modifiers'
            return getattr(self._instance_modifiers, name)

        elif (self._current_build_stage == 'modifiers' or self._current_build_stage == 'filters') and hasattr(self._instance_selectors, name):
            self._current_build_stage = 'selectors'
            return getattr(self._instance_selectors, name)

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")    
    
    def create_wkri_with_datatype_values(
            self, 
            related_prefetch = None,
            lazy = False, 
            callable_get_tiles: Optional[Callable[[], Iterator[TileModel]]] = None
        ):

        permittedNodegroupIds: List[str | None] = self._parent_wrapper_instance._permitted_nodegroups()

        defaultFilterTileAgrs: Dict[str, any] = {
            'nodegroup_id__in': permittedNodegroupIds
        }

        def fallback_get_tiles(**defaultFilterTileAgrs) -> Iterator[TileModel]:
            """
            This method gets an Iterator[TileModel] which are the only tiles permitted towards the user. This method also handles the pagination on the tiles
            however remember that tiles are children of resources so we paginate the resources

            @return: This returns an iteratoring of permitted tiles towards the user
            """

    
            tiles: Iterator[TileModel] = []
            # limit: int | None = args.get('limit', 30)
            # page: int | None = args.get('page', 1)

            # if (page is not None):
            #     resource_ids: List[str] = list(Resource.objects.filter(graph_id=self._parent_wrapper_instance.graphid).values_list("resourceinstanceid", flat=True))
            #     paginator: Paginator = Paginator(resource_ids, limit)
            #     page_obj: Page = paginator.get_page(page)

            #     resource_ids: List[str] = page_obj.object_list
            #     tiles = TileModel.objects.filter(**defaultFilterTileAgrs, resourceinstance__in=resource_ids).select_related('resourceinstance', 'nodegroup').iterator()    

            # else: 
            tiles = TileModel.objects.filter(**defaultFilterTileAgrs).select_related('resourceinstance', 'nodegroup').iterator()  

            return tiles;

        def set_tile_values_and_create_wkris(tiles: Iterator[TileModel]) -> Dict[str, WKRIEntry]:
            """
            This method takes in the tiles which want convert towards Dict[str, WKRIEntry], to allow the mapping of resources and tile data, the creation of
            instances for wkris and the converations towards tile data to datatype classes.

            @param tiles: An iterator of TileModel instances representing resource tiles.
            @return: This returns an iteratoring of permitted tiles towards the user.
            """
            nodes: Iterator[Node] = Node.objects.filter(nodeid__in=permittedNodegroupIds).iterator();
            node_dict: Dict[str, Node] = {node.nodegroup_id: node for node in nodes}
            wkriMapping: Dict[str, WKRIEntry] = {}

            # * Loop all tiles so (n*tiles)
            for tile in tiles:
                # * We get the resource instance from the tile and the node instance from the tiles node gorup
                resource = tile.resourceinstance
                node = node_dict.get(tile.nodegroup_id)

                # * We check if the resource from the tile has already created the wkri
                if (wkriMapping.get(resource.resourceinstanceid)):
                    wkri = wkriMapping[resource.resourceinstanceid]["wkri"]

                # * If not then we create the wkri for the resource and the values oject
                else:
                    wkri = self._parent_wrapper_instance.view_model(
                        id=resource.resourceinstanceid,
                        resource=resource,
                        cross_record=None,
                        related_prefetch=related_prefetch,
                    )

                    wkriMapping[resource.resourceinstanceid] = {
                        "values": {},
                        "wkri": wkri
                    }
                    
                # * Next we convert our value into a datatype class
                pseudo_node = self._parent_wrapper_instance._make_pseudo_node_cls(
                    key=node.alias,
                    # node=node,
                    tile=tile,
                    wkri=wkri
                )

                # ? Here we state that the tile can be converted from a resource to a Tile Datatype Class as again this slows the process
                pseudo_node._convert_tile_resource = True;

                # * We hook up the tile datatype class into values with our key as the node alias
                wkriMapping[resource.resourceinstanceid]["values"][node.alias] = [pseudo_node]

            return wkriMapping


        def set_wkri_value_to_tile_values(wkriMapping: Dict[str, WKRIEntry]) -> List[type]:
            """
            This method handles the converation of all the values for the tile datatype class into a ValueList class which then this ValueList class
            is stored within the wkri instance and finally the method returns all the wkri instances.

            @param wkriMapping: The mapping of wkri towards values
            @return: This returns all the wkri instances within a list
            """

            wkris: List[type] = [];

            # * Loop wkri mapping created from the method above (n*resources)
            for key in wkriMapping:
                # * Extract the wkri instance and values from the mapping
                wkri: type = wkriMapping[key]['wkri'];
                values: dict[str, any] = wkriMapping[key]['values'];

                # * Convert the values into a ValueList instance and attach this onto the wkri instance
                wkri._values = ValueList(
                    values,
                    wkri._,
                    related_prefetch=related_prefetch
                )

                # * Append the wkri instance on a list
                wkris.append(wkri)

            return wkris

        # * Calls our inner methods heree
        tiles = callable_get_tiles(**defaultFilterTileAgrs) if callable_get_tiles else fallback_get_tiles(**defaultFilterTileAgrs)
        wkriMapping = set_tile_values_and_create_wkris(tiles)
        wkris = set_wkri_value_to_tile_values(wkriMapping)

        return wkris
    

    def _build_edges(self):
        if (self._edges_domain_to_range and self._edges_range_to_domain):
            return;

        self._edges_domain_to_range = defaultdict(list)   # domainnode_id -> [rangenode_id]
        self._edges_range_to_domain = defaultdict(list)  # rangenode_id -> [domainnode_id]

        edges = Edge.objects.filter(graph_id=self._parent_wrapper_instance.graphid)
        
        for edge in edges:
            domain = edge["domainnode_id"]
            range_ = edge["rangenode_id"]
            
            self._edges_domain_to_range[domain].append(range_)
            self._edges_range_to_domain[range_].append(domain)

    @property
    def edges_domain_to_range(self):
        self._build_edges
        return self._edges_domain_to_range
    
    @property
    def edges_range_to_domain(self):
        self._build_edges
        return self._edges_range_to_domain