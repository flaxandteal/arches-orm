from __future__ import annotations
from datetime import datetime, timezone
from arches_orm.view_models.datetime import (
    DateTimeViewModel,
)
from ._register import REGISTER

# def handle_date_or_datetime_format(format_key: str, value: str):
#     formats = {
#         "YYYY-MM-DD HH:mm:ssZ": "%Y-%m-%dT%H:%M:%S.%f%z",  # Adjusted to match ISO format
#         "YYYY-MM-DD": "%Y-%m-%d",
#         "YYYY-MM": "%Y-%m",
#         "YYYY": "%Y"
#     }

#     print("VALUE TYPE:", value)

#     if format_key not in formats:
#         raise ValueError(f"Date format not recognized: {value}")

#     try:
#         # Use fromisoformat if value contains T (ISO format with timezone)
#         if "T" in value:
#             parsed_date = datetime.fromisoformat(value)
#         else:
#             parsed_date = datetime.strptime(value, formats[format_key])

#         # Return output based on expected format
#         if format_key == "YYYY-MM-DD":
#             return parsed_date.strftime("%Y-%m-%d")
#         elif format_key == "YYYY-MM":
#             return parsed_date.strftime("%Y-%m")
#         elif format_key == "YYYY":
#             return parsed_date.strftime("%Y")
#         else:
#             return parsed_date.isoformat(timespec="milliseconds")

#     except ValueError as e:
#         raise ValueError(f"Error parsing date {value}: {e}")


@REGISTER("date")
def date(tile, node, value: str | datetime | None, _, __, ___, date_datatype):
    if tile:
        tile.data.setdefault(str(node.nodeid), None)
        if value is not None:
            if isinstance(value, datetime):
                value = value.astimezone()
                value = value.isoformat(timespec="milliseconds")
            tile.data[str(node.nodeid)] = date_datatype.transform_value_for_tile(str(value))

    if not tile or (data := tile.data[str(node.nodeid)]) is None:
        return None

    value = date_datatype.transform_value_for_tile(data)
    # value = handle_date_or_datetime_format(node.config.get("dateFormat"), value)
    # value = _handle_formats(value)
    return DateTimeViewModel.parse(value)


@date.as_tile_data
def e_as_tile_data(value):
    if isinstance(value, datetime):
        value = value.astimezone()
        value = value.isoformat(timespec="milliseconds")
    return str(value)
