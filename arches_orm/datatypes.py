import enum

class DataTypeNames(enum.Enum):
    SEMANTIC = "semantic"
    STRING = "string"
    CONCEPT = "concept"
    CONCEPT_LIST = "concept-list"
    RESOURCE_INSTANCE = "resource-instance"
    RESOURCE_INSTANCE_LIST = "resource-instance-list"
    GEOJSON_FEATURE_COLLECTION = "geojson-feature-collection"
    EDTF = "edtf"
    FILE_LIST = "file-list"
    USER = "user"
    BOOLEAN  = "boolean"
    NUMBER  = "number"
    DATE  = "date"
    URL = "url"
    DOMAIN_VALUE = "domain-value"
    NODE_VALUE = "node-value"
    BNGCENTREPOINT = "bngcentrepoint"
    DOMAIN_VALUE_LIST = "domain-value-list"
    DJANGO_GROUP = "django-group"
