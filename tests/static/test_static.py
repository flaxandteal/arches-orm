from pathlib import Path
from rdflib import RDF
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
def test_can_get_collection_from_concept_scheme(arches_orm):
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
