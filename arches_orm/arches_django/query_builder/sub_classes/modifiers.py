from ..utilities import annotation_key
from typing import List, TYPE_CHECKING
from arches.app.models.models import ResourceXResource, Node, NodeGroup, Edge, TileModel

class QueryBuilderModifier:
    _instance_query_builder = None;
    _wrapper_instance = None;
    _queryset_tiles = None;

    if TYPE_CHECKING:
        from arches_orm.arches_django.query_builder.query_builder import QueryBuilder

    def __init__(self, instance_query_builder):
        self._instance_query_builder = instance_query_builder;
        self._wrapper_instance = instance_query_builder._parent_wrapper_instance;
    
    def order_by(self, *args: List[str]) -> "QueryBuilder":
        """
        Method handles the appending of order by for future filtering within the Django query in the file filters.py

        Returns:
            QueryBuilder: Enables chainable functionality 
        """
        
        nodes: List[Node] = self._wrapper_instance._node_objects_by_alias();

        # * Loops through arguments
        for index in range(len(args)):
            node_alias: str = args[index].replace('-', '');
            node: Node = nodes.get(node_alias)

            # * Sets annotation if the key hasn't been setup for annotation
            self._instance_query_builder.set_annotation(
                node_alias, 
                node
            )

            # * Using annotation provided, then orders by the annotation with appending the annotation onto the orders by from our parent
            self._instance_query_builder._order_by.append(annotation_key(args[index]))
    
        return self._instance_query_builder