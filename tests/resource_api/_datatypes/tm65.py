from arches_orm.view_models import (
    GeoJSONFeatureCollectionViewModel,
)
from arches_orm.resource_api.datatypes._register import REGISTER


@REGISTER("tm65centrepoint")
def tm65_centrepoint(tile, node, value: dict | None, _, __, ___, geojson_feature_collection_datatype):
    if tile:
        tile.data.setdefault(str(node.nodeid), {})
        if value is not None:
            # FIXME: prevent the IDs changing on load
            if isinstance(value, dict):
                tile.data[str(node.nodeid)].update(value)
            else:
                tile.data[str(node.nodeid)] = geojson_feature_collection_datatype.transform_value_for_tile(
                    value
                )

    if not tile or tile.data[str(node.nodeid)] is None:
        return None
    return GeoJSONFeatureCollectionViewModel(tile.data[str(node.nodeid)])


@tm65_centrepoint.as_tile_data
def tm65_as_tile_data(geojson_feature_collection):
    return dict(geojson_feature_collection)
