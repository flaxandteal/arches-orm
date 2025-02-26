from typing import Iterator, Dict, List, TypedDict, Any, Callable, Optional
from arches.app.models.models import TileModel
from django.core.paginator import Paginator, Page
from arches.app.models.resource import Resource
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge, TileModel
from functools import lru_cache
from arches_orm.arches_django.wrapper import ValueList
from django.db.models import Func, F, ExpressionWrapper, FloatField, CharField

from .sub_classes.filters import QueryBuilderFilters
from .sub_classes.selectors import QueryBuilderSelectors
from .sub_classes.modifiers import QueryBuilderModifier

from .expressions import (
    expression_string_datatype, 
    expression_number_datatype, 
    expression_date_datatype, 
    expression_concept_value, 
    expression_boolean_value
)

from .utilities import annotation_key
from collections import defaultdict
from typing import TypedDict

class AnnotationProperties(TypedDict):
    name: str
    values: List[int]

class FilterStructure(TypedDict):
    logical_operator: str
    conditions: Dict[str, any]

ExcludeStructure = FilterStructure

LOAD_ALL_NODES = True

class QueryBuilder:
    _instance = None
    _parent_wrapper_instance = None;

    _instance_filters: QueryBuilderFilters = None;
    _instance_selectors: QueryBuilderSelectors = None;
    _instance_modifiers: QueryBuilderModifier = None;
    _current_build_stage: str = None;

    _edges_domain_to_range: Dict[str, str] = None;
    _edges_range_to_domain: Dict[str, str] = None;

    _filter_structures: List[FilterStructure] = [];
    _exclude_structures: List[ExcludeStructure] = [];

    _annotations: Dict[str, ExpressionWrapper] = {};
    _order_by: List[str] = [];
    _lazy_mode: bool = False

    def __init__(self, parent_wrapper_instance):
        self._parent_wrapper_instance = parent_wrapper_instance;
        self._instance = self;
        self._reset()

        # * Setup instances of filters, modifiers, selectors
        self._instance_filters  = QueryBuilderFilters(self)
        self._instance_modifiers  = QueryBuilderModifier(self)
        self._instance_selectors = QueryBuilderSelectors(self)

    def __getattr__(self, name):
        if not self._current_build_stage and hasattr(self._instance_filters, name):
            return getattr(self._instance_filters, name)

        elif not self._current_build_stage and hasattr(self._instance_modifiers, name):
            self._current_build_stage = 'modifiers'
            return getattr(self._instance_modifiers, name)

        elif (self._current_build_stage == 'modifiers' or not self._current_build_stage) and hasattr(self._instance_selectors, name):
            self._current_build_stage = 'selectors'
            return getattr(self._instance_selectors, name)

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")    

    # ? Some strange reason if I call Person.where(age=30) and then Person.where(age=50), it will still have the previous filters age=30, thus this method
    # ? is born
    def _reset(self): 
        self._filter_structures = []
        self._exclude_structures = []
        self._order_by = []
        self._lazy_mode = False 

    def set_annotation(
        self,
        node_alias: str, 
        node: Node,
        addiontal_keys: List[str] = None 
    ):
        """
        Method adds a annoitation to the _annotations variable, if its not already contained. This gets the expressions by using the methods inside
        expressions.py for each datatype class. Then this _annotations variable is used within the selectors

        Args:
            key (str): The node alias
            node (Node): The node
            addiontal_keys (List[str], optional): Addional keys allowed for example firstname__en__value='Harry'
        """
        if (node_alias in self._annotations):
            return;

        if (node.datatype == 'string'):
            self._annotations[annotation_key(node_alias)] = expression_string_datatype(node.nodeid, addiontal_keys)

        elif (node.datatype == 'number'):
            self._annotations[annotation_key(node_alias)] = expression_number_datatype(node.nodeid)

        elif (node.datatype == 'date'):
            self._annotations[annotation_key(node_alias)] = expression_date_datatype(node.nodeid)

        elif (node.datatype == 'boolean'):
             self._annotations[annotation_key(node_alias)] = expression_boolean_value(node.nodeid)

        elif (node.datatype == 'concept'):
            self._annotations[annotation_key(node_alias)] = expression_concept_value(node)
    

    def create_wkri_with_datatype_values(
            self, 
            related_prefetch = None,
            lazy = False, 
            callback_get_tiles: Optional[Callable[[], Iterator[TileModel]]] = None
        ) -> List[type]:
        """
        This method handles getting tiles, converting tiles to their respected datatype classes, storing these datatype classes within WKRI instances and
        returning WKRI instances within a list. We can also use callbacks to handle getting tiles differently

        Args:
            related_prefetch (_type_, optional): Related prefetch is used for methods on the wrapper.py
            lazy (bool, optional): Lazy is used for methods on the wrapper.py
            callback_get_tiles (Optional[Callable[[], Iterator[TileModel]]], optional): This method is used to handle a callback for getting the tiles
                & this should be mainly used within selectors.py

        Returns:
            List[type]: The list of WKRI instances
        """

        # * These vars are used manally to setup the get tiles methods for the user premitted node groups
        permittedNodegroupIds: List[str | None] = self._parent_wrapper_instance._permitted_nodegroups()
        defaultFilterTileAgrs: Dict[str, any] = {
            'nodegroup_id__in': permittedNodegroupIds
        }

        def _fallback_get_tiles(**defaultFilterTileAgrs) -> Iterator[TileModel]:
            """
            This method is a fallback method for the get tiles, incase a callback_get_tiles is not provided

            @return: This returns an iteratoring of permitted tiles towards the user
            """

            return TileModel.objects.filter(**defaultFilterTileAgrs).select_related('resourceinstance', 'nodegroup').iterator()  

        def _convert_tile_pseudo_nodes_and_create_wkris_with_value_lists(tiles: Iterator[TileModel]) -> List[type]:
            """
            This methods loops through our tiles so (n*tiles), converts the tiles to a pseudo node, then appends the pseudo nodes on a ValustList which
            is stored on a WKRI instance. These WKRI instances are appended on list and that is the return value

            @param tiles: An iterator of TileModel instances representing resource tiles.
            @return: This returns the list of WKRI instances
            """

            # * Gets a Dict of nodes with the node group UUID as the key, as this is the fastest way of gaining the nodes
            nodes: Iterator[Node] = Node.objects.filter(nodeid__in=permittedNodegroupIds).iterator();
            node_dict: Dict[str, Node] = {node.nodegroup_id: node for node in nodes}

            # * Next we have our return value and a mapping of index within wkris with the key as resource ids
            wkri_resource_instance_mapping_wkris_index: Dict[str, int] = {}
            wkris: List[type] = []; # * Return value

            def _get_wkri_index_nor_create_wkri_instance(resource) -> int:
                """
                This method will create a new WKRI or if the WKRI has already been previsouly created, then it finds the index.

                Args:
                    resource (ResourceObject): This is the resource which the tile is related towards

                Returns:
                    int: The WKRI index within the List wkris
                """
                nonlocal wkris, wkri_resource_instance_mapping_wkris_index

                # * If the resource id is not contained within mapping, it means there is no WKRI instance towrads this tile as of yet
                # * therefore we must create this WKRI and append/map towards our variables
                current_wkri_index = wkri_resource_instance_mapping_wkris_index.get(resource.resourceinstanceid)

                if current_wkri_index is not None:
                    return current_wkri_index

                # * Create WKRI and hook up ValueList towards the wkri values
                wkri = self._parent_wrapper_instance.view_model(
                    id=resource.resourceinstanceid,
                    resource=resource,
                    cross_record=None,
                    related_prefetch=related_prefetch,
                )

                wkri._values = ValueList(
                    {},
                    wkri._,
                    related_prefetch=related_prefetch
                )

                # * Save the WKRI instances so we can reuse the instances
                wkris.append(wkri)
                wkri_resource_instance_mapping_wkris_index[resource.resourceinstanceid] = len(wkris) - 1

                return wkri_resource_instance_mapping_wkris_index.get(resource.resourceinstanceid)

            def _set_node_value_within_value_list(wkri, current_wkri_index: int, node: Node, tile: TileModel):
                """
                Method handles registering the node value to a datatype class/view model and then attaches this dataype class/view model to a ValueList 
                class instance. Moreover, if lazy loading is enabled, then we just only care about the nodegroup alias which the node is related towards
                and we attach that onto a Dict within the ValueList with the value being False. Lazy does not load the dataype class/view model on the value
                and will only proceed with this option if the user access the value for example Person.name[0].full_name[0]

                Args:
                    wkri (WKRI): This is the well known resource instance, related to the Tile
                    current_wkri_index (int): This is the current index of the wkri within wkris, which is gained from _get_wkri_index_nor_create_wkri_instance
                    node (Node): This is the node which the tile is related towards
                    tile (TileModel): This is the tile record itself, containing the database data
                """
                nonlocal node_dict, wkris
                if self._lazy_mode:
                    nodegroup = node_dict.get(tile.nodegroup.nodegroupid)

                    wkri._._values.__setitem__(nodegroup.alias, False)
                    wkris[current_wkri_index] = wkri

                else:
                    # * Convert the tile to a pseudo node
                    pseudo_node = self._parent_wrapper_instance._make_pseudo_node_cls(
                        key=node.alias,
                        # node=node,
                        tile=tile,
                        wkri=wkri
                    )

                    # ? Here we state that the tile can be converted from a resource to a Tile Datatype Class as again this slows the process
                    pseudo_node._convert_tile_resource = True;

                    # * Append on the wkri values and update the WKRI within our return value list
                    wkri._._values.__setitem__(node.alias, [pseudo_node])
                    wkris[current_wkri_index] = wkri
                    print('PSEUDO NODE VALUE ', pseudo_node._value)

            # * Loop all tiles so (n*tiles)
            for tile in tiles:
                # * We get the resource instance from the tile and the node instance from the tiles node gorup
                resource = tile.resourceinstance
                node = node_dict.get(tile.nodegroup_id)

                current_wkri_index = _get_wkri_index_nor_create_wkri_instance(resource);
                wkri = wkris[current_wkri_index];

                print('INSIDE TILES : ', tile.data.get('9718f941-950e-11ea-a048-f875a44e0e11'))
                print('current_wkri_index : ', current_wkri_index)
                print('resourceinstance : ', resource.resourceinstanceid)
                print('node : ', node.alias)

                print('------------------------------')

                _set_node_value_within_value_list(wkri, current_wkri_index, node, tile)

            return wkris

        # * We first need to quire the tiles so we use the callback_get_tiles and if one is not provided then we use _fallback_get_tiles as a default.
        # * Either way we get the tiles
        tiles = callback_get_tiles(**defaultFilterTileAgrs) if callback_get_tiles else _fallback_get_tiles(**defaultFilterTileAgrs)

        # for tile in tiles:
        #     print('INSIDE TILES : ', tile.data.get('9718f941-950e-11ea-a048-f875a44e0e11'))

        # # ! I'm not too sure why but once 
        # for tile in tiles:
        #     temp = tile 

        # * Next we convert the tiles towards pseudo nodes, store the pseudo nodes inside ValueList and store the ValueList inside a instance of WKRI
        # * Finally we return a list of WKRIs
        result = _convert_tile_pseudo_nodes_and_create_wkris_with_value_lists(tiles)
        for data in result:
            print('FINAL : ', data.system_reference_numbers.primaryreferencenumber.primary_reference_number)

        print('===================================')

        return result
    

    def _build_edges(self):
        """
        Method builds the edges if required, if the edges already exisit then its returned. The purpose is we can find the next node forward or backwards
        """
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
    def edges_domain_to_range(self) -> Dict[str, str]:
        """
        Getter method to return edges towards the domain to range

        Returns:
            Dict[str, str]: returns the edges domain to range
        """
        self._build_edges
        return self._edges_domain_to_range
    
    @property
    def edges_range_to_domain(self) -> Dict[str, str]:
        """
        Getter method to return edges towards the range to domain

        Returns:
            Dict[str, str]: Returns the edges range to domain
        """
        self._build_edges
        return self._edges_range_to_domain