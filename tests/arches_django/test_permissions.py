import pytest
from arches_orm.adapter import get_adapter
from unittest.mock import patch

@pytest.fixture
def User():
    from django.contrib.auth.models import User
    return User

@pytest.fixture
def owner(User):
    user_account = User(email="owner@example.com")
    user_account.save()
    return user_account

@pytest.mark.django_db
@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("deny_activity", [False, True])
def test_can_attach_related_then_save(arches_orm, lazy, owner, User, person_ash, deny_activity):
    from arches_orm.arches_django.wrapper import get_permitted_nodegroups

    with get_adapter().context_free() as cvar:
        person_ashs = person_ash.save()
        record_status_ids = [
            str(arches_orm.models.Activity._node_objects_by_alias()[key].nodegroup_id)
            for key in ("record_status", "record_status_assignment")
        ]

    n = 0
    for record_status in (False, True):
        def png(user):
            assert user == owner
            perms = list(arches_orm.models.Person._nodegroup_objects())
            if not deny_activity:
                perms += list(arches_orm.models.Activity._nodegroup_objects())
            if record_status:
                perms += record_status_ids
            return perms

        with (
            patch("arches_orm.arches_django.wrapper.get_permitted_nodegroups", png) as _,
            patch("arches_orm.arches_django.wrapper.user_can_read_resource", lambda user, resource: True) as __,
            patch("arches_orm.arches_django.wrapper.user_can_read_graph", lambda user, graph: True) as __,
            patch("arches_orm.arches_django.wrapper.user_can_edit_resource", lambda user, resource: True) as ___
        ):
            with get_adapter().context(user=owner) as cvar:
                reloaded_person = arches_orm.models.Person.find(person_ashs.id)
                activity = arches_orm.models.Activity()
                # Can save as long as permitted or, at least, no nodegroups have changed that are not.
                activity.save()

                if deny_activity and not record_status:
                    with pytest.raises(AttributeError) as _:
                        StatusEnum = activity.record_status_assignment.record_status.__collection__
                else:
                    StatusEnum = activity.record_status_assignment.record_status.__collection__
                    activity.record_status_assignment.record_status = StatusEnum.BacklogDashSkeleton
                    activity.save()

                person_ashs.associated_activities.append(activity)
                n += 1
                assert len(person_ashs.associated_activities) == n
                person_ashs.save()
                assert len(person_ashs.associated_activities) == n
                reloaded_person = arches_orm.models.Person.find(person_ashs.id)
                assert len(reloaded_person.associated_activities) == n
                assert isinstance(reloaded_person.associated_activities[-1], arches_orm.models.Activity)

@pytest.mark.django_db
@pytest.mark.parametrize("lazy", [False, True])
def test_can_only_view_permissioned_resources(arches_orm, lazy, owner, User, person_ash):
    ...
