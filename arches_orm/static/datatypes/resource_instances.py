from typing import Any, Generator
import re
import json
from collections import UserDict
from uuid import UUID
from pathlib import Path

from pydantic import BaseModel

_RESOURCE_LOCATIONS: dict[UUID, Path] = {}

class StaticResourceInstanceInfo(BaseModel):
    descriptors: dict[str, dict[str, str]]
    graph_id: UUID
    graph_publication_id: UUID | None
    legacyid: None | UUID
    name: str
    principaluser_id: UUID | None
    resourceinstanceid: UUID
    publication_id: UUID | None

StaticProvisionalEdit = Any
class StaticTile(BaseModel):
    data: dict[UUID, dict[str, Any] | list[Any] | None]
    nodegroup_id: UUID
    resourceinstance_id: UUID
    tileid: UUID
    parenttile_id: UUID | None = None
    provisionaledits: None | list[StaticProvisionalEdit] = None
    sortorder: int | None = None

class StaticResource(BaseModel):
    resourceinstance: StaticResourceInstanceInfo
    tiles: list[StaticTile]

class StaticStore(UserDict[str | UUID, StaticResource]):
    _node_tile_index: dict[str, dict[tuple[str, str], str]]

    def __init__(self, *args, **kwargs):
        self._node_tile_index = {}
        super().__init__(*args, **kwargs)

    def search_by_nodeid(self, nodeid: str | UUID | None = None, resourceid: str | UUID | None = None, regex: str | None = None, case_i: bool = False) -> Generator[tuple[UUID, UUID], None, None]:
        # TODO: replace with something more efficient
        flags = re.I if case_i else 0
        if regex is not None:
            rx = re.compile(regex, flags)
        if nodeid is not None:
            nodeid = str(nodeid)
        if resourceid is not None:
            resourceid = str(resourceid)
        for node_index_id, tile_index in self._node_tile_index.items():
            if nodeid is not None and nodeid != node_index_id:
                continue
            for (resource_id, tile_id), tile_data in tile_index.items():
                if resourceid is not None and resourceid != resource_id:
                    continue
                if regex is not None and rx.match(tile_data):
                    yield UUID(resource_id), UUID(tile_id)

    def add_to_node_tile_index(self, resource: dict[str, Any]):
        for tile in resource["tiles"]:
            if tile["data"]:
                for nodeid, value in tile["data"].items():
                    self._node_tile_index.setdefault(nodeid, {})
                    self._node_tile_index[nodeid][(resource["resourceinstance"]["resourceinstanceid"], tile["tileid"])] = json.dumps(value)

    def get(self, item: str | UUID, default: None | StaticResource = None) -> StaticResource | None:
        if isinstance(item, str):
            item = UUID(item)
        resource = super().get(item)
        if resource is None:
            if (path := _RESOURCE_LOCATIONS.get(item)):
                with path.open() as f:
                    for resource_json in json.load(f)["business_data"]["resources"]:
                        resource = StaticResource(**resource_json)
                        self[resource.resourceinstance.resourceinstanceid] = resource
        return resource

    def load_all(self) -> None:
        for resource_id in _RESOURCE_LOCATIONS:
            if resource_id not in self:
                self.get(resource_id)

def scan_resource_path(resource_root: Path, load_data_to_index: bool=True) -> None:
    if resource_root.is_dir():
        for fname in resource_root.iterdir():
            if fname.suffix == ".json":
                scan_resource_path(fname)
    else:
        with resource_root.open() as f:
            resource_file = json.load(f)

        for resource_json in resource_file["business_data"]["resources"]:
            _RESOURCE_LOCATIONS[UUID(resource_json["resourceinstance"]["resourceinstanceid"])] = resource_root
            if load_data_to_index:
                STATIC_STORE.add_to_node_tile_index(resource_json)

STATIC_STORE = StaticStore()
