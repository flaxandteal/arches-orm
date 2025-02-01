# Dummy module, to house dynamically generated
# resource models.
from .wkrm import get_resource_models_for_adapter

_MODEL_CLASSES = set()

def reload():
    global _MODEL_CLASSES
    for mc in _MODEL_CLASSES:
        del globals()[mc]
    resource_models = get_resource_models_for_adapter()["by-class"]
    _MODEL_CLASSES = set(resource_models)
    globals().update(resource_models)
reload()
