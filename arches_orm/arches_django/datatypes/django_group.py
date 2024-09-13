import logging
from django.contrib.auth.models import Group

from arches_orm.view_models import (
    GroupViewModelMixin,
    GroupProtocol,
)
from ._register import REGISTER

logger = logging.getLogger(__name__)


class DjangoGroupViewModel(Group, GroupViewModelMixin):
    class Meta:
        proxy = True
        app_label = "arches-orm"
        db_table = Group.objects.model._meta.db_table

    def __bool__(self):
        # We have to do this as we do not have a concept of an empty node
        return bool(self.pk)


@REGISTER("django-group")
def django_group(tile, node, value, _, __, ___, group) -> GroupProtocol:
    group = None
    value = (value if not isinstance(value, tuple) else value[0]) or tile.data.get(str(node.nodeid))
    pk = None
    if value:
        if isinstance(value, Group):
            if value.pk:
                value = value.pk
            else:
                group = DjangoGroupViewModel()
                group.__dict__.update(value.__dict__)
        if value:
            try:
                pk = int(value)
                group = DjangoGroupViewModel.objects.get(pk=int(value))
            except DjangoGroupViewModel.DoesNotExist:
                logger.warning("Django Group is missing for pk value %s", str(value))
    if not group:
        group = DjangoGroupViewModel()
        group.pk = pk
    return group


@django_group.as_tile_data
def dg_as_tile_data(view_model):
    return view_model.pk
