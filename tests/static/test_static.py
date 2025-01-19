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
    groups = Group.all()
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

@context_free
def test_can_hydrate_a_resource(arches_orm):
    from arches_orm.models import Group
    group = Group._.from_dict({"name": "My Group"})
    group.save()
    resource_json = group._.resource.model_dump_json()
    with (Path(__file__).parent / "_artifacts" / "export_test_group.json").open() as f:
        reference_dict = json.load(f)
    reference_dict["business_data"]["resources"][0]["resourceinstance"]["name"] = "My Group"
    tiles = reference_dict["business_data"]["resources"][0]["tiles"][:1]
    tiles[0]["data"] = {
        "127095f5-c05e-11e9-bb57-a4d18cec433a": {"en": {"direction": "ltr", "value": "My Group"}}
    }
    reference_dict["business_data"]["resources"][0]["tiles"] = tiles
    _compare_exported_json(resource_json, reference_dict)

@context_free
def test_can_use_edtf(arches_orm):
    from arches_orm.models import Group
    group = Group._.from_dict({"date_of_publication": ["2024-01-01"]})
    group.save()
    resource_json = group._.resource.model_dump_json()
    with (Path(__file__).parent / "_artifacts" / "export_test_group.json").open() as f:
        reference_dict = json.load(f)
    reference_dict["business_data"]["resources"][0]["resourceinstance"]["name"] = "Undefined"
    tiles = reference_dict["business_data"]["resources"][0]["tiles"][:1]
    tiles[0]["data"] = {
        "a2e1623c-01ee-4ab1-a2c7-cc9f623d624f": "2024-01-01"
    }
    tiles[0]["nodegroup_id"] = "a2e1623c-01ee-4ab1-a2c7-cc9f623d624f"
    reference_dict["business_data"]["resources"][0]["tiles"] = tiles
    _compare_exported_json(resource_json, reference_dict)

@context_free
def test_can_save_with_concept(arches_orm):
    from arches_orm.models import Group
    group = Group.create()
    permission = group.permissions.append()
    ActionEnum = permission.action.__collection__
    permission.action = [ActionEnum.Reading]
    group.save()
    resource_json = json.loads(group._.resource.model_dump_json())
    assert resource_json["tiles"][0]["data"] == {
        "7cb692b2-7072-11ee-bb7a-0242ac140008": ["e3a6493e-5df4-4ad4-a699-ade7ccf01917"]
    }
    permission.action = ["Reading"]
    group.save()

@context_free
def test_can_make_consistent_uuids(arches_orm):
    from arches_orm.models import Group
    def _cb(resource):
        return f"{resource._._name}-{'/'.join(map(str, resource.date_of_publication))}"
    Group.set_unique_identifier_cb(_cb)

    group = Group._.from_dict({"name": "My Group", "date_of_publication": ["2024-01-01"]})
    group.save()
    resource_json = json.loads(group._.resource.model_dump_json())
    assert resource_json["resourceinstance"]["resourceinstanceid"] == "d181337f-8efa-4de4-1c7c-91592010a44d"
