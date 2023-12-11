from arches.app.models.resource import Resource
from datetime import datetime
from arches.app.models.models import ResourceXResource, Node
from arches.app.models.tile import Tile as TileProxyModel
from arches.app.models.system_settings import settings as system_settings
from .relations import RelationList
from .view_models import ConceptValueViewModel, UserViewModel, StringViewModel


LOAD_FULL_NODE_OBJECTS = True
LOAD_ALL_NODES = True


class TranslationMixin:
    """Provides functionality for translating to/from Arches types."""

    def fill_from_resource(self, reload=None, related_prefetch=None):
        """Populate fields from the ID-referenced Arches resource."""

        all_values = {}
        cls = self.__class__
        nodes = cls._build_nodes()
        class_nodes = {node["nodeid"]: key for key, node in nodes.items()}
        if reload is True or (reload is None and self._lazy):
            self.resource = Resource.objects.get(resourceinstanceid=self.id)
        self.resource.load_tiles()

        for tile in self.resource.tiles:
            semantic_values = {}
            semantic_node = None
            for nodeid in tile.data:
                if nodeid in class_nodes:
                    key = class_nodes[nodeid]
                    node = nodes[key]
                    if LOAD_FULL_NODE_OBJECTS:
                        node_obj = cls._node_objects()[nodeid]
                    else:
                        node_obj = Node(
                            pk=nodeid,
                            nodeid=nodeid,
                            nodegroup_id=node["nodegroupid"],
                            graph_id=self.graphid,
                        )
                    (
                        datatype,
                        datatype_name,
                        multiple_values,
                    ) = node["datatype"]

                    lang = node.get("lang", None)
                    if "/" in key:
                        _semantic_node, key = key.split("/")
                        if semantic_node is None:
                            semantic_node = _semantic_node
                        elif semantic_node != _semantic_node:
                            raise RuntimeError(
                                "We should never end up with node values from two"
                                " groups (semantic nodes) in a tile:"
                                f" {semantic_node} and {_semantic_node}"
                            )
                        if "/" in semantic_node:
                            raise NotImplementedError(
                                "No support for nested semantic nodes currently"
                            )
                        values = semantic_values
                    else:
                        values = all_values

                    if datatype_name in ("resource-instance", "resource-instance-list"):
                        from .utils import attempt_well_known_resource_model

                        if isinstance(tile.data[nodeid], list):
                            values[key] = RelationList(self, key, nodeid)
                            for datum in tile.data[nodeid]:
                                if (
                                    related := attempt_well_known_resource_model(
                                        datum["resourceId"],
                                        related_prefetch,
                                        x=datum,
                                        lazy=True,
                                    )
                                ) is not None:
                                    values[key]["value"].append(related, tile)
                        elif tile.data[nodeid]:
                            values[key] = {
                                "tile": tile,
                                "value": attempt_well_known_resource_model(
                                    tile.data[nodeid],
                                    related_prefetch,
                                    x=datum,
                                    lazy=True,
                                ),
                            }
                    elif datatype.datatype_name == "string":
                        text = self._make_string_from_tile_and_node(tile, node_obj)
                        if multiple_values:
                            values.setdefault(key, [])
                            values[key].append({"value": text, "tile": tile})
                        else:
                            values[key] = {"value": text, "tile": tile}
                    elif datatype.datatype_name == "concept-list":
                        values[key] = {
                            "value": [
                                self.make_concept(concept_id)
                                for concept_id in tile.data[nodeid]
                                if concept_id
                            ],
                            "tile": tile,
                        }
                    elif datatype.datatype_name == "concept":
                        values[key] = {
                            "tile": tile,
                            "value": (
                                self.make_concept(tile.data[nodeid])
                                if tile.data[nodeid]
                                else None
                            ),
                        }
                    elif datatype.datatype_name == "user":
                        value = self._make_user_from_tile_and_node(tile, node_obj)
                        if multiple_values:
                            values.setdefault(key, [])
                            values[key].append({"tile": tile, "value": value})
                        else:
                            values[key] = {"tile": tile, "value": value}
                    elif datatype.collects_multiple_values():
                        values[key] = {
                            "tile": tile,
                            "value": datatype.to_json(tile, node_obj),
                        }
                    else:
                        value = datatype.get_display_value(
                            tile, node_obj, language=lang
                        )
                        if multiple_values:
                            values.setdefault(key, [])
                            values[key].append({"tile": tile, "value": value})
                        else:
                            values[key] = {"tile": tile, "value": value}
            if semantic_node:
                all_values.setdefault(str(semantic_node), [])
                all_values[str(semantic_node)].append(
                    {"tile": tile, "value": semantic_values}
                )
        self._values.update(all_values)
        self._filled = True

    @classmethod
    def _make_user_from_tile_and_node(cls, tile, node):
        """Provide a rich user object."""

        string_datatype = cls._datatype_factory().get_instance("user")
        return UserViewModel(tile, node, string_datatype)

    @classmethod
    def _make_string_from_tile_and_node(cls, tile, node):
        """Provide a string object that can have language, while remaining a string."""

        string_datatype = cls._datatype_factory().get_instance("string")
        return StringViewModel(tile, node, string_datatype)

    @classmethod
    def make_concept(cls, concept_id):
        """Provide a concept object.

        It that can retain taxonomic information, while remaining a string.
        """

        concept_datatype = cls._datatype_factory().get_instance("concept")
        return ConceptValueViewModel(concept_id, concept_datatype)

    def _update_tiles(self, tiles, values, tiles_to_remove, prefix=None):
        """Map data in the well-known resource back to the Arches tiles."""

        relationships = []
        for key, node in self._nodes.items():
            if prefix is not None:
                if not key.startswith(prefix):
                    continue
                prekey, key = key.split("/", -1)
                if "/" in prekey:
                    raise NotImplementedError("Only one level of groupings supported")
            elif "/" in key:
                continue

            if key in values:
                data = {}
                single = False
                value = values[key]
                datatype, datatype_name, multiple_values = node["datatype"]
                if value is None:
                    continue

                # FIXME: this change needs checked
                if datatype_name == "semantic" and multiple_values:
                    tiles.setdefault(node["nodegroupid"], [])
                    if "parentnodegroup_id" in node:
                        parent = tiles.setdefault(
                            node["parentnodegroup_id"],
                            [
                                TileProxyModel(
                                    dict(
                                        data={},
                                        nodegroup_id=node["parentnodegroup_id"],
                                        tileid=None,
                                    )
                                )
                            ],
                        )[0]
                    else:
                        parent = None
                    for entry in value:
                        subtiles = {}
                        if parent:
                            subtiles[parent.nodegroup_id] = [parent]

                        # If we have a dataless version of this node, perhaps because it
                        # is already a parent, we allow it to be filled in.
                        if (
                            tiles[node["nodegroupid"]]
                            and not tiles[node["nodegroupid"]][0].data
                            and tiles[node["nodegroupid"]][0].tiles
                        ):
                            subtiles[node["nodegroupid"]] = [
                                tiles[node["nodegroupid"]][0]
                            ]

                        relationships += self._update_tiles(
                            subtiles, entry["value"], tiles_to_remove, prefix=f"{key}/"
                        )
                        if node["nodegroupid"] in subtiles:
                            tiles[node["nodegroupid"]] = list(
                                set(tiles[node["nodegroupid"]])
                                | set(subtiles[node["nodegroupid"]])
                            )
                    # We do not need to do anything here, because
                    # the nodegroup (semantic node) has no separate existence from the
                    # values in the tile in our approach -- if there were values, the
                    # appropriate tile(s) were added with this nodegroupid. For nesting,
                    # this would need to change.
                    continue
                elif (
                    value
                    and (isinstance(value, list) or isinstance(value, RelationList))
                    and isinstance(value[0], TranslationMixin)
                ):
                    value = [({}, v) for v in value]
                    relationships += value
                    value = [[v] for v, _ in value]
                # FIXME: we should be able to remove entries if appropriate
                elif (
                    isinstance(value, list) or isinstance(value, RelationList)
                ) and len(value) == 0:
                    continue
                elif datatype:
                    if multiple_values:
                        single = False
                        value = [
                            {
                                "tile": val["tile"],
                                "value": datatype.transform_value_for_tile(
                                    val["value"], **node.get("config", {})
                                ),
                            }
                            for val in value
                        ]
                    else:
                        single = True
                        value = datatype.transform_value_for_tile(
                            value, **node.get("config", {})
                        )
                if single:
                    multiple_values: list = [value]
                else:
                    multiple_values: list = list(value)

                for value in multiple_values:
                    data = {}
                    data[node["nodeid"]] = value["value"]
                    old_tile = value["tile"]
                    if not single and prefix:
                        raise RuntimeError(
                            "Cannot have field multiplicity inside a grouping (semantic"
                            " node), as it is equivalent to nesting"
                        )

                    if "parentnodegroup_id" in node:
                        parents = tiles.setdefault(
                            node["parentnodegroup_id"],
                            [
                                TileProxyModel(
                                    dict(
                                        data={},
                                        nodegroup_id=node["parentnodegroup_id"],
                                        tileid=None,
                                    )
                                )
                            ],
                        )
                        parent = parents[0]
                    else:
                        parent = None

                    if node["nodegroupid"] in tiles:
                        # if single or not tiles[node["nodegroupid"]].data:
                        if single:
                            tile = tiles[node["nodegroupid"]][0]
                            if tile in tiles_to_remove:
                                tiles_to_remove.remove(tile)
                            if parent and not tile.parenttile:
                                tile.parenttile = parent
                                parent.tiles.append(tile)
                            tile.data.update(data)
                            continue

                    tile = old_tile or TileProxyModel(
                        dict(
                            data=data,
                            nodegroup_id=node["nodegroupid"],
                            parenttile=parent,
                            tileid=None,
                        )
                    )
                    tile.data = data
                    tiles.setdefault(node["nodegroupid"], [])
                    if tile not in tiles[node["nodegroupid"]]:
                        tiles[node["nodegroupid"]].append(tile)
                    if parent and tile not in parent.tiles:
                        parent.tiles.append(tile)
        return relationships

    def to_resource(
        self,
        verbose=False,
        strict=False,
        _no_save=False,
        _known_new=False,
        _do_index=True,
    ):
        """Construct an Arches resource.

        This may be new or existing, for this well-known resource.
        """

        resource = Resource(resourceinstanceid=self.id, graph_id=self.graphid)
        tiles = {}
        if not _known_new:
            for tile in TileProxyModel.objects.filter(resourceinstance=resource):
                tiles.setdefault(str(tile.nodegroup_id), [])
                tiles[str(tile.nodegroup_id)].append(tile)
        tiles_to_remove = sum((ts for ts in tiles.values()), [])

        relationships = self._update_tiles(tiles, self._values, tiles_to_remove)

        # parented tiles are saved hierarchically
        resource.tiles = [
            t
            for t in sum((ts for ts in tiles.values()), [])
            if not t.parenttile and t not in tiles_to_remove
        ]
        for tile in tiles_to_remove:
            if tile.tileid:
                tile.delete()

        if not resource.createdtime:
            resource.createdtime = datetime.now()
        # errors = resource.validate(verbose=verbose, strict=strict)
        # if len(errors):
        #    raise RuntimeError(str(errors))

        # FIXME: potential consequences for thread-safety
        # This is required to avoid e.g. missing related models preventing
        # saving (as we cannot import those via CSV on first step)
        self._pending_relationships = []
        if not _no_save:
            bypass = system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION
            system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION = True
            # all_tiles = resource.tiles
            # parentless_tiles = [tile for tile in all_tiles if not tile.parenttile]
            ## This only solves the problem for _one_ level of nesting
            # if len(all_tiles) > len(parentless_tiles):
            #    resource.tiles = parentless_tiles
            #    resource.save()
            #    resource.tiles = all_tiles

            resource.save()
            self.id = resource.resourceinstanceid
            system_settings.BYPASS_REQUIRED_VALUE_TILE_VALIDATION = bypass
        elif not resource._state.adding:
            self.id = resource.resourceinstanceid

        self.resource = resource

        # for nodegroupid, nodeid, resourceid in relationships:
        for value, related in relationships:
            related.to_resource(verbose=verbose, strict=strict, _no_save=_no_save)
            if _no_save:
                self._pending_relationships.append((value, related, self))
            else:
                # TODO: what happens if the cross already exists for some reason?
                cross = ResourceXResource(
                    resourceinstanceidfrom=resource,
                    resourceinstanceidto=related.resource,
                )
                cross.save()
                value.update(
                    {
                        "resourceId": str(resource.resourceinstanceid),
                        "ontologyProperty": "",
                        "resourceXresourceId": str(cross.resourcexid),
                        "inverseOntologyProperty": "",
                    }
                )
                resource.save()

        return resource
