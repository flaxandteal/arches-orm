from pathlib import Path
from rdflib import RDF
from io import BytesIO
from rdflib.namespace import SKOS
from arches_orm.adapter import context_free, get_adapter
from arches_orm.static.datatypes.concepts import concept_to_skos

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
    rdm.save_concept(my_status, "/tmp/test.xml")
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
