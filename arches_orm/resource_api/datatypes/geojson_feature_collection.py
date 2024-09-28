from arches_orm.view_models import (
    GeoJSONFeatureCollectionViewModel,
)
from ._register import REGISTER


@REGISTER("geojson-feature-collection")
def geojson_feature_collection(tile, node, value: dict | None, _, __, ___, geojson_feature_collection_datatype):
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


@geojson_feature_collection.as_tile_data
def gj_as_tile_data(geojson_feature_collection):
    return dict(geojson_feature_collection)
