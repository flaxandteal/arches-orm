import enum
from . import utils

DataTypeNames = enum.Enum(
    "DataTypeNames",
    [(es.name, es.value) for es in utils.StandardDataTypeNames]
    + [(key, value) for key, (value, _) in utils._CUSTOM_DATATYPES.items()]
)

COLLECTS_MULTIPLE_VALUES = {
    DataTypeNames.CONCEPT_LIST,
    DataTypeNames.FILE_LIST,
    DataTypeNames.DOMAIN_VALUE_LIST,
    DataTypeNames.RESOURCE_INSTANCE_LIST,
}
COLLECTS_MULTIPLE_VALUES |= {DataTypeNames(key) for key, (_, c) in utils._CUSTOM_DATATYPES.items() if c}

# Prevent further custom datatypes being added.
utils._CUSTOM_DATATYPES = None
