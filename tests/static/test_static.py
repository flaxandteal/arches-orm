from pathlib import Path
from rdflib import RDF
from io import BytesIO
from rdflib.namespace import SKOS
from arches_orm import static
import json
from typing import Any
from jsondiff import diff
from arches_orm.adapter import context_free, get_adapter
from arches_orm.static.datatypes.concepts import concept_to_skos, load_collection_path
from arches_orm.static.datatypes.resource_instances import StaticResource

@context_free
def test_can_get_collection(arches_orm):
    StatusEnum = get_adapter().get_collection("7849cd3c-3f0d-454d-aaea-db9164629641")
    assert StatusEnum.BacklogDashSkeleton

@context_free
def test_can_make_collection(arches_orm):
    rdm = get_adapter().get_rdm()
    concept_1 = rdm.make_simple_concept("My Status", "Backlog - Nothing")
    concept_2 = rdm.make_simple_concept("My Status", "Backlog - Everything")
    my_status = rdm.make_simple_concept("My Status", children=[concept_1, concept_2])
    MyStatusEnum = rdm.concept_to_collection(my_status)
    assert MyStatusEnum.BacklogDashEverything

@context_free
def test_can_save_collection(arches_orm):
    rdm = get_adapter().get_rdm()
    concept_1 = rdm.make_simple_concept("My Status", "Backlog - Nothing")
    concept_2 = rdm.make_simple_concept("My Status", "Backlog - Everything")
    my_status = rdm.make_simple_concept("My Status", children=[concept_1, concept_2])
    MyStatusEnum = rdm.concept_to_collection(my_status)
    stream = BytesIO()
    rdm.save_concept(my_status, stream)
    assert "My Status" in bytes(stream.getbuffer()).decode("utf-8")
    rdm.update_collections(MyStatusEnum, Path("/tmp/collections.xml"))

@context_free
def test_can_insert_into_concept_scheme(arches_orm):
    rdm = get_adapter().get_rdm()
    nismr_value = rdm.get_concept("23be33d2-c1c2-479b-b37a-603b474ce9aa")
    NISMR = rdm.concept_to_collection(nismr_value)
    assert NISMR.Dow037
    graph = concept_to_skos(nismr_value.concept, "localhost:8000")
    found = False
    for concept, _, _ in graph.triples((None, RDF.type, SKOS.Concept)):
        for _, _, label in graph.triples((concept, SKOS.prefLabel, None)):
            label = str(label)
            if "DOW 037" in label and "ded50ba1-9051-4cef-9da4-eabca689b9a7" in label:
                found = True
                break
        if found:
            break
    assert found

@context_free
def test_can_update_fish_concept(arches_orm):
    rdm = get_adapter().get_rdm()
    fish_value = rdm.get_concept("844b63f0-27e3-358d-9362-147379fc3420")
    FISHMonuments = rdm.concept_to_collection(fish_value)
    assert FISHMonuments.CistercianNunnery
    graph = concept_to_skos(fish_value.concept, "localhost:8000")
    rdm.save_concept(fish_value, "/tmp/concept.xml")
    found = False

    parent = None
    for concept, _, _ in graph.triples((None, RDF.type, SKOS.Concept)):
        for _, _, label in graph.triples((concept, SKOS.prefLabel, None)):
            label = str(label)
            if "Cistercian Nunnery" in label and "5c858c23-c51d-444c-ac8d-bdf60ee2fc6b" in label:
                found = concept
            if "Nunnery" in label and "485fa3b3-b098-4a48-92de-68de152cc450" in label:
                parent = concept

    assert found
    assert parent

    for _, _, label in graph.triples((found, SKOS.altLabel, None)):
        if "Cistercian Abbey" in str(label):
            break
    else:
        raise AssertionError("AltLabel not found")

    for _, _, label in graph.triples((found, SKOS.related, None)):
        if "eda3537a-2ecd-3dbd-a702-63dbc6f51905" in str(label):
            break
    else:
        raise AssertionError("Relationship not found")

    for _, _, label in graph.triples((found, SKOS.scopeNote, None)):
        if "An abbey or a priory of Cistercian nuns." in str(label):
            break
    else:
        raise AssertionError("Relationship not found")

    for _, _, label in graph.triples((parent, SKOS.narrower, None)):
        if "875c129b-d23f-35dc-ae57-15226b8c4a12" in str(label):
            break
    else:
        raise AssertionError("Child relationship not found")

def test_can_derive_a_new_collection():
    rdm = get_adapter().get_rdm()
    StatusEnum = rdm.get_collection("7849cd3c-3f0d-454d-aaea-db9164629641")
    concept_1 = rdm.make_simple_concept("My Status", "Done")
    StatusEnum = rdm.derive_collection("7849cd3c-3f0d-454d-aaea-db9164629641", include=[concept_1], exclude=[StatusEnum.BacklogDashSkeleton.value])
    assert len(StatusEnum.__members__) == 3
    assert StatusEnum.Done

@context_free
def test_can_replace_collection(arches_orm):
    rdm = get_adapter().get_rdm()
    concept_1 = rdm.make_simple_concept("Monuments", "My Monument")
    StatusEnum = rdm.derive_collection("b82ee4cf-2f90-4dab-bed7-bda3feaf6d64", include=[concept_1])
    stream = BytesIO()
    rdm.export_collection(StatusEnum, stream)
    assert f"http://arches:8000/{concept_1.conceptid}" in bytes(stream.getbuffer()).decode("utf-8")

@context_free
def test_can_search_for_collection(arches_orm):
    rdm = get_adapter().get_rdm()
    assert rdm.find_collection_by_label("Record Status")

@context_free
def test_can_search_for_concept(arches_orm):
    rdm = get_adapter().get_rdm()
    assert rdm.find_concept_by_label("Cistercian Nunnery")

@context_free
def test_can_load_collections_xml(arches_orm):
    collections = Path("../coral-arches/coral/pkg/reference_data/collections/collections.xml")
    load_collection_path(collections)

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
