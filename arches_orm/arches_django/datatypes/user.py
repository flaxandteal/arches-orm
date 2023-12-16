
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


class UserViewModel(User, UserViewModelMixin):
    class Meta:
        proxy = True
        app_label = "arches-orm"
        db_table = User.objects.model._meta.db_table


@REGISTER("user")
def user(tile, node, value, _, __, user_datatype) -> UserProtocol:
    user = None
    value = value or tile.data.get(str(node.nodeid))
    if value:
        if isinstance(value, User):
            if value.pk:
                value = value.pk
            else:
                user = UserViewModel()
                user.__dict__.update(value.__dict__)
        if value:
            user = UserViewModel.objects.get(pk=int(value))
    if not user:
        user = UserViewModel()
    return user


@user.as_tile_data
def u_as_tile_data(view_model):
    return view_model.pk

