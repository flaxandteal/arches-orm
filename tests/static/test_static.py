from pathlib import Path
import json
from typing import Any
from jsondiff import diff
from arches_orm.adapter import context_free, get_adapter
from arches_orm.static.datatypes.resource_instances import StaticResource

@context_free
def test_can_get_collection():
    StatusEnum = get_adapter().get_collection("7849cd3c-3f0d-454d-aaea-db9164629641")
    assert StatusEnum.BacklogDashSkeleton

@context_free
def test_can_make_collection():
    rdm = get_adapter().get_rdm()
    concept_1 = rdm.make_simple_concept("My Status", "Backlog - Nothing")
    concept_2 = rdm.make_simple_concept("My Status", "Backlog - Everything")
    my_status = rdm.make_simple_concept("My Status", children=[concept_1, concept_2])
    MyStatusEnum = rdm.concept_to_collection(my_status)
    assert MyStatusEnum.BacklogDashEverything

@context_free
def test_can_save_collection():
    rdm = get_adapter().get_rdm()
    concept_1 = rdm.make_simple_concept("My Status", "Backlog - Nothing")
    concept_2 = rdm.make_simple_concept("My Status", "Backlog - Everything")
    my_status = rdm.make_simple_concept("My Status", children=[concept_1, concept_2])
    MyStatusEnum = rdm.concept_to_collection(my_status)
    rdm.save_concept(my_status, "/tmp/test.xml")
    rdm.update_collections(MyStatusEnum, Path("/tmp/collections.xml"))

@context_free
def test_can_load_resource_models(arches_orm):
    from arches_orm.models import Group
    Group.all()

@context_free
def test_can_load_a_resource(arches_orm):
    from arches_orm.models import Group
    groups = Group.all()
    assert str(groups[0]) == "Global Group"

@context_free
def test_can_create_a_resource(arches_orm):
    from arches_orm.models import Person
    ash = Person()
    name = ash.name.append()
    name.full_name = "Ash"
    assert name.full_name._value == {"en": {"direction": "ltr", "value": "Ash"}} # type: ignore

@context_free
def test_can_search_for_a_resource(arches_orm):
    from arches_orm.models import Group
    groups = list(Group._.where(name=".*Global Group.*"))
    assert len(groups) == 1
    for group in groups:
        assert group.basic_info[0].name == "Global Group"
        assert group.statement[0].description == "Global root of group hierarchy."

@context_free
def test_can_get_text_in_language(arches_orm):
    from arches_orm.models import Group
    with get_adapter("static").context() as cx:
        # TODO check ga search
        cx.get()["language"] = "ga"
        groups = list(Group._.where(name=".*Global Group.*"))
        assert len(groups) == 1
        for group in groups:
            assert group.basic_info[0].name == "Grúpa Domhanda"

        cx.get()["language"] = "en"
        groups = list(Group._.where(name=".*Global Group.*"))
        assert len(groups) == 1
        for group in groups:
            assert group.basic_info[0].name == "Global Group"


def _compare_exported_json(resource_json: str, reference_dict: dict[str, Any]):
    resource = {
        "business_data": {
            "resources": [
                json.loads(resource_json)
            ]
        }
    }
    dff = diff(resource, reference_dict)
    uuids = {}
    # This lets us say which UUIDs should be the same, even if we do not
    # care about the specific value. The format is <UUID:1> etc.
    def _find_uuids(res: dict[str, Any], ref: dict[str, Any], seg: dict[str, Any]) -> None:
        for key, value in seg.items():
            res_value = res[key]
            ref_value = ref[key]
            if isinstance(value, str) and value.startswith("<UUID:") and value:
                if value not in uuids:
                    uuids[value] = res_value
                ref[key] = uuids[value]
            elif isinstance(value, dict) and type(ref_value) is type(res_value):
                _find_uuids(res_value, ref_value, value)
            else:
                dff = diff(resource, reference_dict, syntax="symmetric")
                assert not dff, json.dumps(dff, indent=2)
    _find_uuids(resource, reference_dict, dff)
    dff = diff(resource, reference_dict, syntax="symmetric")
    assert not dff, json.dumps(dff, indent=2)

@context_free
def test_can_export_a_resource(arches_orm):
    from arches_orm.models import Group
    groups = list(Group._.where(name=".*Global Group.*"))
    assert len(groups) == 1
    group = groups[0]
    group.save()
    resource_json = group._.resource.model_dump_json()

    with (Path(__file__).parent / "_artifacts" / "export_test_group.json").open() as f:
        reference_dict = json.load(f)
    _compare_exported_json(resource_json, reference_dict)

    from arches_orm.models import Person
    ash = Person()
    name = ash.name.append()
    name.full_name = "Ash"
    ash.save()
    resource_json = ash._.resource.model_dump_json()

    with (Path(__file__).parent / "_artifacts" / "export_test_person.json").open() as f:
        reference_dict = json.load(f)
    _compare_exported_json(resource_json, reference_dict)
