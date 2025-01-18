from __future__ import annotations

import httpx
from enum import Enum
from lxml import etree as ET
import json
from urllib.parse import urlparse, urlunparse
from uuid import UUID
from pathlib import Path
from typing import TypedDict, Any, Literal
try:
    from typing import NotRequired
except ImportError: # 3.9
    from typing_extensions import NotRequired

from pydantic import BaseModel
from arches_orm.adapter import get_adapter
from arches_orm.collection import make_collection, CollectionEnum
from arches_orm.utils import consistent_uuid as cuuid
from arches_orm.view_models.concepts import ConceptValueViewModel

_MODELS: dict[UUID, dict[str, Any]] = {}

DEFAULT_LANGUAGE: str = "en"

StaticTranslatableString = str

def _(string: str | StaticTranslatableString):
    if isinstance(string, str):
        return string
    return string[DEFAULT_LANGUAGE]

class StaticNodeGroup(BaseModel):
    legacygroupid: None
    nodegroupid: UUID
    parentnodegroup_id: UUID | None
    cardinality: Literal["1", "n", None]

class StaticNode(BaseModel):
    alias: str | None
    config: dict[str, Any]
    datatype: str
    description: str | None
    exportable: bool
    fieldname: None | str
    graph_id: UUID
    hascustomalias: bool
    is_collector: bool
    isrequired: bool
    issearchable: bool
    istopnode: bool
    name: str
    nodegroup_id: UUID | None
    nodeid: UUID
    parentproperty: str | None = None
    sortorder: int
    ontologyclass: str | None = None
    sourcebranchpublication_id: None | UUID = None

class StaticConstraint(BaseModel):
    card_id: UUID
    constraintid: UUID
    nodes: list[UUID]
    uniquetoallinstances: bool

class StaticCard(BaseModel):
    active: bool
    cardid: UUID
    component_id: UUID
    config: None | dict[str, Any]
    constraints: list[StaticConstraint]
    cssclass: None | str
    description: str | None | StaticTranslatableString
    graph_id: UUID
    helpenabled: bool
    helptext: StaticTranslatableString
    helptitle: StaticTranslatableString
    instructions: StaticTranslatableString
    is_editable: bool
    name: StaticTranslatableString
    nodegroup_id: UUID
    sortorder: int | None
    visible: bool

class StaticCardsXNodesXWidgets(BaseModel):
    card_id: UUID
    config: dict[str, Any]
    id: UUID
    label: StaticTranslatableString
    node_id: UUID
    sortorder: int | None
    visible: bool
    widget_id: UUID

class StaticEdge(BaseModel):
    description: None
    domainnode_id: UUID
    edgeid: UUID
    graph_id: UUID
    name: None | str
    rangenode_id: UUID
    ontologyproperty: None | str =  None

class StaticFunctionsXGraphs(BaseModel):
    config: dict[str, Any]
    function_id: UUID
    graph_id: UUID
    id: UUID

class StaticPublication(BaseModel):
    graph_id: UUID
    notes: None | str
    publicationid: UUID
    published_time: str

class StaticRoot(BaseModel):
    alias: str
    config: dict[str, Any]
    datatype: str
    description: StaticTranslatableString
    exportable: bool
    fieldname: None | str
    graph_id: UUID
    hascustomalias: bool
    is_collector: bool
    isrequired: bool
    issearchable: bool
    istopnode: bool
    name: str
    nodegroup_id: None | UUID
    nodeid: UUID
    ontologyclass: str | None
    sortorder: int
    sourcebranchpublication_id: None | UUID

class StaticGraph(BaseModel):
    author: str
    cards: list[StaticCard] | None = None
    cards_x_nodes_x_widgets: list[StaticCardsXNodesXWidgets] | None = None
    color: str | None
    config: dict[str, Any]
    deploymentdate: None | str
    deploymentfile: None | str
    description: StaticTranslatableString
    edges: list[StaticEdge]
    functions_x_graphs: list[StaticFunctionsXGraphs] | None = None
    graphid: UUID
    iconclass: str
    is_editable: bool | None = None
    isresource: bool
    jsonldcontext: str | None
    name: StaticTranslatableString
    nodegroups: list[StaticNodeGroup]
    nodes: list[StaticNode]
    ontology_id: UUID | None
    publication: StaticPublication | None = None
    relatable_resource_model_ids: list[UUID]
    resource_2_resource_constraints: list[Any] | None = None
    slug: str | None
    subtitle: StaticTranslatableString
    template_id: UUID
    version: str


_GRAPHS: dict[UUID, StaticGraph] = {}

def retrieve_graph(graph: str | UUID) -> StaticGraph:
    if isinstance(graph, str):
        graph = UUID(graph)
    return _GRAPHS[graph]

DELVING = True
def load_models() -> WKRM:
    wkrms: list[dict[str, Any]] = []
    adapter = get_adapter("resource_api")
    client = httpx.Client(**adapter.config.get("client", {}))
    if DELVING:
        graph_jsons = client.get(
            "/api/arches/graphs?format=arches-json&hide_empty_nodes=false&compact=false",
        )
        graph_jsons = graph_jsons.json()
        graphs = {str(graph_id): name for graph_id, name in graph_jsons["models"].items()}
    else:
        graph_jsons = client.get(
            "/graphs?format=arches-json&hide_empty_nodes=false&compact=false",
        ).json()
        graphs = {str(graph_json["graphid"]): graph_json["name"] for graph_json in graph_jsons if graph_json["isresource"]}
    for graph_id in sorted(graphs):
        if DELVING:
            graph_body_json = client.get(
                f"/graphs/{graph_id}?format=arches-json&gen="
            ).json()
            graph = StaticGraph(**graph_body_json)
        else:
            graph_body_json = client.get(
                f"/graphs/{graph_id}?format=arches-json&hide_empty_nodes=false&compact=false&cards=false&exclude=cards",
            ).json()
            graph = StaticGraph(**graph_body_json["graph"])
        _GRAPHS[graph.graphid] = graph

        print(graph.name)
        wkrms.append(
            {
                "model_name": _(graph.name),
                "graphid": graph.graphid,
                "remapping": None,
            }
        )
    return wkrms
