# MIT License
#
# Copyright (c) 2020 Taku Fukada, 2022 Phil Weir

import os
import threading
from arches.app.models.graph import Graph
from asgiref.sync import sync_to_async

from arches_orm.utils import snake

import graphene

from aiodataloader import DataLoader
from arches_orm.wkrm import WELL_KNOWN_RESOURCE_MODELS

from arches.app.models import models
from arches.app.models.concept import Concept
from django.utils.translation import get_language

LANG = get_language() or "en"
ALLOW_NON_WKRM_GRAPHS = str(os.environ.get("ARCHES_GRAPH_API_ALLOW_NON_WKRM_GRAPHS", "false")).lower() == "true"


class DataTypes:
    inited = False

    def __init__(self):
        self.graphs = {}

    def init(self):
        allowed_graphs = None if ALLOW_NON_WKRM_GRAPHS else {wkrm.graphid for wkrm in WELL_KNOWN_RESOURCE_MODELS}
        self.node_datatypes = {str(nodeid): datatype for nodeid, datatype in models.Node.objects.values_list("nodeid", "datatype")}
        self.node_concepts = {}
        self.graphs = {
            str(name): pk for pk, name in Graph.objects.values_list("pk", "name")
            if (allowed_graphs is None or str(pk) in allowed_graphs)
        }
        for graphid in self.graphs.values():
            self.node_concepts.update({
                str(node_id): config["rdmCollection"]
                for node_id, config in
                models.Node.objects.filter(graph_id=graphid).exclude(config__rdmCollection__isnull=True).values_list("nodeid", "config")
            })

data_types = DataTypes()

# Do synchronous data retrieval of "constants". After this, we assume they are available.
thread = threading.Thread(target=data_types.init)
thread.start()
thread.join()

class ResourceModelLoader(DataLoader):
    async def batch_load_fn(self, keys):
        # Here we call a function to return a user for each key in keys
        out = list(await sync_to_async(self._batch_load_fn_real)(keys))
        return out

    def _batch_load_fn_real(self, keys):
        return [Concept().get_child_collections(key, depth_limit=1) for key in keys]

concept_loader = ResourceModelLoader()


_name_map = {
    snake(key): key
    for key in data_types.graphs
}

class ResourceModelQuery(graphene.ObjectType):
    build_graph = graphene.JSONString(resource_model=graphene.String())

    get_available_graphs = graphene.List(graphene.String)

    async def resolve_get_available_graphs(self, info):
        return list(_name_map.values())

    async def resolve_build_graph(self, info, resource_model):
        graph = data_types.graphs[resource_model]
        graph = await sync_to_async(Graph.objects.get)(pk=graph)

        def _format_node(node):
            details = {
                "name": node.name,
                "nodeid": str(node.pk),
                "nodegroupid": str(node.nodegroup_id),
                "datatype": str(data_types.node_datatypes[str(node.pk)]),
                "alias": node.alias
            }
            if str(node.pk) in data_types.node_concepts:
                details["concept"] = data_types.node_concepts[str(node.pk)]
            return details
        def _to_atree(ent):
            return [
                (_format_node(child['node']), _to_atree(child))
                for child in ent['children']
            ]

        tree = graph.get_tree()
        return _to_atree(tree)
