from geojson import FeatureCollection, GeoJSON
from ._base import (
    ViewModel,
)


class GeoJSONFeatureCollectionViewModel(FeatureCollection, ViewModel):
    """Wraps a geometry."""

    def __new__(cls, value: dict):
        geojson = value if isinstance(value, GeoJSON) else GeoJSON(value)
        instance = GeoJSON.to_instance(geojson)
        if not isinstance(instance, GeoJSON):
            raise RuntimeError(f"Can only create feature collections, not {type(instance)}")
        return instance
