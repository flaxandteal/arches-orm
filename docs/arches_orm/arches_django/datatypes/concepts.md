# Module arches_orm.arches_django.datatypes.concepts

??? example "View Source"

        import uuid

        from typing import Any, Callable

        from functools import cached_property

        from django.contrib.auth.models import User

        from arches.app.models.models import Node, ResourceInstance

        from arches.app.models.tile import Tile

        from arches.app.models.resource import Resource

        from collections import UserDict

        from arches_orm.view_models import (

            WKRI,

            UserViewModelMixin,

            UserProtocol,

            StringViewModel,

            RelatedResourceInstanceListViewModel,

            RelatedResourceInstanceViewModelMixin,

            ConceptListValueViewModel,

            ConceptValueViewModel,

            SemanticViewModel,

        )

        from ._register import REGISTER

        @REGISTER("concept-list")

        def concept_list(tile, node, value: list[uuid.UUID | str] | None, _, __):

            if value is not None:

                tile.data = value

            make_cb = REGISTER.make(tile, node, value=value)

            return ConceptListValueViewModel(tile.data, make_cb)

        

        @concept_list.as_tile_data

        def cl_as_tile_data(concept_list):

            return [x.as_tile_data() for x in concept_list]

        

        @REGISTER("concept")

        def concept_value(tile, node, value: uuid.UUID | str | None, __, ___, datatype):

            if value is not None:

                tile.data[str(node.nodeid)] = value

            concept_value_cb = datatype.get_value

            if tile.data[str(node.nodeid)] is None:

                return None

            return ConceptValueViewModel(tile.data[str(node.nodeid)], concept_value_cb)

        

        @concept_value.as_tile_data

        def cv_as_tile_data(concept_value):

            return str(concept_value._concept_value_id)

## Variables

```python3
cl_as_tile_data
```

```python3
cv_as_tile_data
```