import logging
from django.contrib.auth.models import User

from arches_orm.view_models import (
    UserViewModelMixin,
    UserProtocol,
)
from ._register import REGISTER

logger = logging.getLogger(__name__)


class UserViewModel(User, UserViewModelMixin):
    class Meta:
        proxy = True
        app_label = "arches-orm"
        db_table = User.objects.model._meta.db_table

    def __bool__(self):
        # We have to do this as we do not have a concept of an empty node
        return bool(self.pk)


@REGISTER("user")
def user(tile, node, value, _, __, ___, user_datatype) -> UserProtocol:
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
            try:
                user = UserViewModel.objects.get(pk=int(value))
            except UserViewModel.DoesNotExist:
                logger.warning("User is missing for pk value %s", str(value))
    if not user:
        user = UserViewModel()
    return user


@user.as_tile_data
def u_as_tile_data(view_model):
    return view_model.pk
