# MIT License
#
# Copyright (c) 2020 Taku Fukada, 2022 Phil Weir

import os
import threading
import logging
import io
import uuid
from asgiref.sync import sync_to_async

from arches_orm.adapter import context_free

import graphene
from graphene_file_upload.scalars import Upload

from aiodataloader import DataLoader
from arches_orm.wkrm import get_resource_models_for_adapter
from arches_orm.datatypes import DataTypeNames
from arches_orm.arches_django.datatypes.concepts import invalidate_collection, retrieve_collection

from arches.app.utils.skos import SKOSReader
from arches.app.models import models
from arches.app.models.concept import Concept
from django.utils.translation import get_language

from arches.app.datatypes.datatypes import DataTypeFactory

TERM_SEP = "》"
LANG = get_language() or "en"
ALLOW_NON_WKRM_CONCEPTS = str(os.environ.get("ARCHES_GRAPH_API_ALLOW_NON_WKRM_CONCEPTS", "false")).lower() == "true"


class DataTypes:
    node_datatypes = None
    inited = False

    def __init__(self):
        self.collections = {}
        self.remapped = {}

    def retrieve_raw_collection(self, key):
        collection = Concept().get_child_collections_hierarchically(key, query="")
        return collection

    def retrieve_collection(self, key):
        invalidate_collection(key)
        self.collections[key] = retrieve_collection(key)
        return self.collections[key]

    @context_free
    def init(self):
        if not self.inited:
            self.node_datatypes = {str(nodeid): datatype for nodeid, datatype in models.Node.objects.values_list("nodeid", "datatype")}
            self.node_aliases = {str(nodeid): alias for nodeid, alias in models.Node.objects.values_list("nodeid", "alias")}
            self.node_concepts = {}
            self.datatype_factory = DataTypeFactory()

        concept_keys = {}
        for name, wkrm in get_resource_models_for_adapter()["by-class"].items():
            concepts = {}
            for field, info in dict(wkrm.__fields__).items():
                if info["type"] in (DataTypeNames.CONCEPT, DataTypeNames.CONCEPT_LIST):
                    if info["node"].value is None:
                        logging.warning("Cannot instantiate concept %s for %s in field %s", info["nodeid"], name, field)
                        continue
                    key = info["node"].value._collection_id
                    try:
                        self.collections[key] = info["node"].value.__collection__
                    except models.Concept.DoesNotExist:
                        logging.warning("Cannot find concept %s for %s in field %s", key, name, field)
                        continue
                    concepts[info["nodeid"]] = key
            for nodeid, key in concepts.items():
                if key is None:
                    continue
                concept_keys.setdefault(key, [])
                concept_keys[key].append((wkrm._._model_class_name, nodeid))

data_types = DataTypes()

# Do synchronous data retrieval of "constants". After this, we assume they are available.
thread = threading.Thread(target=data_types.init)
thread.start()
thread.join()

class ConceptLoader(DataLoader):
    async def batch_load_fn(self, keys):
        # Here we call a function to return a user for each key in keys
        out = list(await sync_to_async(self._batch_load_fn_real)(keys))
        return out

    def _batch_load_fn_real(self, keys):
        return [Concept().get_child_collections(key, depth_limit=1) for key in keys]

class ConceptSchema(graphene.ObjectType):
    id = graphene.UUID()
    label = graphene.String()
    slug = graphene.String()
    nodetype = graphene.String()

# We try to avoid using IDs, if reasonably possible.
# Terms are an artificial construct to make basic API interaction simple
# (if very limited) They exist as one Concept in relationship to a (.*)parent
class TermSchema(graphene.ObjectType):
    label = graphene.String()
    identifier = graphene.String()
    full_label = graphene.List(graphene.String)
    slug = graphene.String()
    language = graphene.String()
    parent_concept = ConceptSchema

concept_loader = ConceptLoader()


_name_map = {
    collection.__name__: collection.__original_name__
    for collection in data_types.collections.values()
}

_full_concept_query_methods = {}
for converted_concept_name, concept_name in _name_map.items():
    _full_concept_query_methods[converted_concept_name] = graphene.List(graphene.String)

def map_name_or_id_to_key(name_or_id):
    keys = [key for key, collection in data_types.collections.items() if collection.__name__ == name_or_id]
    if len(keys) == 1:
        key = keys[0]
    elif len(keys) > 1:
        raise ValueError("Name matches multiple concepts")
    else:
        try:
            key = str(uuid.UUID(name_or_id))
        except ValueError:
            raise KeyError("Passed name or UUID not found")
    return key

class ConceptQuery(graphene.ObjectType):
    get_terms = graphene.List(TermSchema, concept_name_or_id=graphene.String())
    get_term_list = graphene.List(graphene.String, concept_name_or_id=graphene.String())
    get_concept = graphene.Field(ConceptSchema, name_or_id=graphene.String())
    get_concept_details = graphene.JSONString(name_or_id=graphene.String())

    get_available_concepts = graphene.List(graphene.String)

    async def resolve_get_concept(self, info, name_or_id):
        key = map_name_or_id_to_key(name_or_id)

        if key not in data_types.collections:
            raise KeyError("Unknown concept: may simply not be used by a well-known resource model field")

        concept = await sync_to_async(Concept().get)(
            id=key,
            include_subconcepts=False,
            include_parentconcepts=False,
            include=["label"],
            up_depth_limit=1,
            semantic=False,
        )

        return {
            "id": concept.id,
            "slug": data_types.collections[concept.id].__name__,
            "label": data_types.collections[concept.id].__original_name__,
            "nodetype": concept.nodetype,
        }

    async def resolve_get_concept_details(self, info, name_or_id):
        key = map_name_or_id_to_key(name_or_id)

        if key not in data_types.collections:
            raise KeyError("Unknown concept: may simply not be used by a well-known resource model field")

        concept = await sync_to_async(Concept().get)(
            id=key,
            include_subconcepts=True,
            include_parentconcepts=True,
            include=["label"],
            up_depth_limit=1,
            semantic=False,
        )

        return {
            "id": concept.id,
            "slug": data_types.collections[concept.id].__name__,
            "label": data_types.collections[concept.id].__original_name__,
            "nodetype": concept.nodetype,
            # TODO: turn into a ConceptObject
            "subconcepts": [(sc.id, data_types.collections.get(str(sc.id), None).__name__) for sc in concept.subconcepts],
            "parentconcepts": [(sc.id, data_types.collections.get(str(sc.id), None).__name__) for sc in concept.parentconcepts],
            "relatedconcepts": [(sc.id, data_types.collections.get(str(sc.id), None).__name__) for sc in concept.relatedconcepts],
            "available_nodes": [(model_class_name, data_types.node_aliases[nodeid], nodeid) for model_class_name, nodeid in data_types.concept_keys[concept.id]]
        }


    async def resolve_get_available_concepts(self, info):
        return list(_name_map.values())

    async def resolve_get_term_list(self, info, concept_name_or_id):
        key = map_name_or_id_to_key(concept_name_or_id)
        collection = data_types.collections[key]
        concepts = [term.value for term in collection]
        return [concept.enum for concept in concepts]

    async def resolve_get_terms(self, info, concept_name_or_id, depth=1):
        key = map_name_or_id_to_key(concept_name_or_id)
        collection = data_types.collections[key]
        concepts = [term.value for term in collection]
        terms = []

        def _load_concept(concept):
            return {
                "label": concept.text,
                "identifier": concept._concept_value_id,
                "slug": concept.enum,
                "full_label": [concept.text],
                "language": concept.lang,
            }
        for concept in concepts:
            term = await sync_to_async(_load_concept)(concept)
            terms.append(term)

        return terms


class ConceptInput(graphene.InputObjectType):
    id = graphene.UUID(required=False, default=None)
    label = graphene.String(required=False, default=None)


class ReplaceFromSKOS(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        file = Upload(required=True)

    async def mutate(self, info, file, **kwargs):
        def get_result(skosfile):
            # AGPL Arches
            skos = SKOSReader()
            try:
                rdf = skos.read_file(skosfile)
                ret = skos.save_concepts_from_skos(rdf, "overwrite")
                return ret
            except Exception as e:
                logging.error(str(e)[0:1000])
                return False

        file = io.BytesIO(await file.read())
        result = await sync_to_async(get_result)(file)

        return ReplaceFromSKOS(ok=bool(result))

class AddTerm(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        concept = ConceptInput()
        identifier = graphene.String()

    async def mutate(self, info, concept, identifier):
        if not concept.id:
            if concept.label:
                concept.id = map_name_or_id_to_key(concept.label)

        if not concept.id or concept.id not in data_types.collections:
            raise KeyError("Could not find concept by ID or label to attach term")

        full_label = identifier.split(TERM_SEP)

        collection = data_types.collections[concept.id]
        if full_label[0] not in (collection.__name__, collection.__original_name__):
            raise ValueError("It looks like this identifier does not match this concept")

        collection = await sync_to_async(data_types.retrieve_raw_collection)(concept.id)
        rows = [(value["value"], depth, value["conceptid"]) for value, depth, _, _ in collection]

        found = 1
        parentid = concept.id
        for (label, n, conceptid) in rows:
            if found == n:
                if full_label[found] == label:
                    if len(full_label) - 2 == n:
                        parentid = conceptid
                    if len(full_label) - 1 == n:
                        raise ValueError("Already found a term with this identifier in the hierarchy")
                    else:
                        found += 1

        if found != len(full_label) - 1:
                raise KeyError(f"Could not find a hierarchy level from your identifier (depth={found})")

        # parent = await sync_to_async(Concept().get)(id=parentid)
        def get_result():
            parent = Concept().get(
                id=parentid,
                include_subconcepts=True,
                include_parentconcepts=True,
                include=["label"],
                up_depth_limit=1,
                semantic=False,
            )
            new_concept = Concept()
            new_concept.load({
                "nodetype": "Concept",
                "relationshiptype": "member"
            })
            new_concept.addvalue({
                "type": "prefLabel",
                "category": "label",
                "value": full_label[-1]
            })
            parent.addsubconcept(new_concept)
            new_concept.save()
            parent.save()
            parent.bulk_index()
        await sync_to_async(get_result)()
        await sync_to_async(data_types.retrieve_collection)(concept.id)

        return AddTerm(ok=True)

class FullConceptMutation(graphene.ObjectType):
    add_term = AddTerm.Field()
    replace_from_skos = ReplaceFromSKOS.Field()
