from typing import Any, Generator
from urllib import parse
from dataclasses import field
import httpx
import json
from collections import UserDict
from uuid import UUID
from pathlib import Path
from arches_orm.adapter import get_adapter
from .concepts import DEFAULT_LANGUAGE

from pydantic import BaseModel

_RESOURCE_LOCATIONS: dict[UUID, Path] = {}

StaticProvisionalEdit = Any
class StaticTile(BaseModel):
    data: dict[UUID, dict[str, Any] | list[Any] | None | int | float | bool | str]
    nodegroup_id: UUID
    resourceinstance_id: UUID
    tileid: UUID
    parenttile_id: UUID | None = None
    provisionaledits: None | list[StaticProvisionalEdit] = None
    sortorder: int | None = None

class APIResourceInstanceInfo(BaseModel):
    descriptors: dict[str, dict[str, str]]
    graph_id: UUID
    name: str
    resourceinstanceid: UUID
    publication_id: UUID | None = None
    principaluser_id: int | None = None
    legacyid: None | UUID = None
    graph_publication_id: UUID | None = None
    tiles: list[StaticTile] | None = None

class APIRemoteStore:
    _node_tile_index: dict[str, dict[tuple[str, str], str]]

    def __init__(self, *args: Any, **kwargs: Any):
        self._node_tile_index = {}
        super().__init__(*args, **kwargs)

    @property
    def _client(self):
        adapter = get_adapter("resource_api")
        return httpx.Client(**adapter.config.get("client", {}))

    def __getitem__(self, item):
        return self.get(item)

    def get_tiles(self, resourceid: str | UUID | None, *nodegroup_ids: tuple[str | UUID, str] | None) -> Generator[tuple[UUID, UUID], None, None]:
        query = {
            "resource_ids": json.dumps([str(resourceid)]),
            "nodegroup_ids": json.dumps([str(ng) for ng in nodegroup_ids or []]),
            "format": "arches-json",
            "hide_empty_nodes": False,
            "compact": True,
            "tiles": False
        }
        tiles_json = self._client.get(
            f'/api/tiles?{parse.urlencode(query)}'
        ).json()
        tiles = [StaticTile(**tile) for tile in tiles_json]
        return tiles

    def search_by_nodeids(self, *nodeids: tuple[str | UUID, str] | None) -> Generator[tuple[UUID, UUID], None, None]:
        # TODO: replace with something more efficient
        query = {"op": "and"}
        for (nodeid, value) in nodeids:
            query[str(nodeid)] = {"op": "eq", "lang": "en", "val": str(value)}
        # [{"op"%3A"and"%2C"f3cc1685-185b-11eb-821c-f875a44e0e11"%3A{"op"%3A"eq"%2C"val"%3A""}%2C"f3cc1684-185b-11eb-9a07-f875a44e0e11"%3A{"op"%3A"~"%2C"lang"%3A"en"%2C"val"%3A"group"}%2C"f3cc1687-185b-11eb-aa18-f875a44e0e11"%3A{"op"%3A"eq"%2C"val"%3A""}}]
        query = json.dumps([query])
        url = f'/search/resources?paging-filter=1&tiles=false&advanced-search={parse.quote_plus(query)}'
        results = self._client.get(
            url,
        ).json()
        for result in results["results"]["hits"]["hits"]:
            yield APIResourceInstanceInfo(
                resourceinstanceid=result["_source"]["resourceinstanceid"],
                descriptors={
                    result["_source"].get("displayname_language", DEFAULT_LANGUAGE): {
                        descriptor: str(result["_source"][descriptor_key])
                        for descriptor, descriptor_key in {
                            "name": "displayname",
                            "description": "displaydescription",
                            "map_popup": "map_popup",
                        }.items()
                    }
                },
                name=result["_source"]["displayname"],
                graph_id=result["_source"]["graph_id"],
            )

    def get(self, item: str | UUID, default: None | APIResourceInstanceInfo = None) -> APIResourceInstanceInfo | None:
        if not isinstance(item, str):
            item = str(item)
        resource_json = self._client.get(
            f"/resources/{item}?format=arches-json&hide_empty_nodes=false&compact=false",
        ).json()
        resource = APIResourceInstanceInfo(**resource_json)
        return resource

    def load_all(self, graphid: UUID, limit: int | None=None) -> list[APIResourceInstanceInfo]:
        resource_jsons = self._client.get(
            f"/resources?graph_uuid={graphid}&format=arches-json&hide_empty_nodes=false&compact=false&limit={limit or 0}",
        ).json()
        resources = [
            APIResourceInstanceInfo(**resource_json)
            for resource_json in resource_jsons
        ]
        return resources

STATIC_STORE: APIRemoteStore = APIRemoteStore()
