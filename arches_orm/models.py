# Dummy module, to house dynamically generated
# resource models.
from .wkrm import get_resource_models_for_adapter

def reload():
    globals().update(get_resource_models_for_adapter()["by-class"])
reload()
