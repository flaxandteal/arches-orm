# EXPERIMENTAL
# Contains AGPLv3+ code from the Arches project. Original code
# is made available also under AGPLv3+ license.
#
# MIT License acknowledgement: certain contributions in this file
#     are copyright (c) 2020 Taku Fukada

import os
import threading
import logging
from functools import partial
from asgiref.sync import sync_to_async


from arches_orm.utils import snake, string_to_enum

import graphene
from graphene_file_upload.scalars import Upload

from aiodataloader import DataLoader
from arches_orm.wkrm import attempt_well_known_resource_model, get_well_known_resource_model_by_class_name
from arches_orm.wkrm import WELL_KNOWN_RESOURCE_MODELS
from arches_orm.wkrm import get_resource_models_for_adapter

from arches.app.models import models
from arches.app.models.concept import Concept
import arches.app.models.resource

from arches.app.datatypes.datatypes import DataTypeFactory
from arches_orm.datatypes import DataTypeNames
from arches_orm.utils import is_unset
from starlette_context import context

ALLOW_ANONYMOUS = os.environ.get("ALLOW_ANONYMOUS", False)

if ALLOW_ANONYMOUS:
    logging.error("WARNING: YOU HAVE ALLOWED ANONYMOUS ADMINISTRATIVE ACCESS")

class UserType(graphene.ObjectType):
    user_id = graphene.Int()
    email = graphene.String()

class UserInputType(graphene.InputObjectType):
    user_id = graphene.Int(required=True)
    email = graphene.String(required=False)

class DataTypes:
    node_datatypes = None
    inited = False
    exc = None

    def __init__(self):
        self.collections = {}
        self.graphs = {}
        self.remapped = {}
        self.demapped = {}
        self.semantic_nodes = {}
        self.related_nodes = {}

    def demap(self, model, field, value):
        if is_unset(value):
            return None
        if (closure := self.demapped.get((model, field), None)):
            res = closure(value)
            return res
        return value

    def remap(self, model, field, value):
        if (closure := self.remapped.get((model, field), None)):
            return closure(value)
        return value

    def _build_related(self, nodeid, related_field, model_name):
        node = models.Node.objects.get(nodeid=nodeid)
        if nodeid not in self.related_nodes:
            assert str(nodeid) in self.node_datatypes and self.node_datatypes[str(nodeid)].startswith("resource-instance")
            self.related_nodes[nodeid] = {}
            logging.error("N %s %s", str(node), str(node.config))
            self.related_nodes[nodeid] = {
                "name": related_field,
                "model_name": model_name,
                "relatable_graphs": []
            }
        assert related_field.split("/")[-1] == self.related_nodes[nodeid]["name"].split("/")[-1], f"{related_field} != {self.related_nodes[nodeid]['name']}"
        self.related_nodes[nodeid]["relatable_graphs"] += [str(graph["graphid"]) for graph in node.config["graphs"] if str(graph["graphid"]) in self.graphs]
        logging.error(">%s", str(self.related_nodes[nodeid]["relatable_graphs"]))
        return self.related_nodes[nodeid]["name"]

    def _build_semantic(self, field, subfield, field_info, model_name, model_class_name):
        semantic_type = (model_class_name, field)
        if semantic_type not in self.semantic_nodes:
            self.semantic_nodes[semantic_type] = {
                "name": field,
                "model_name": model_name,
                "model_class_name": model_class_name,
                "fields": []
            }
        self.semantic_nodes[semantic_type]["fields"].append((subfield, field_info))
        assert field == self.semantic_nodes[semantic_type]["name"]
        assert model_class_name == self.semantic_nodes[semantic_type]["model_class_name"]
        return self.semantic_nodes[semantic_type]["name"]

    def init(self):
        if not self.inited:
            try:
                self.node_datatypes = {str(nodeid): datatype for nodeid, datatype in models.Node.objects.values_list("nodeid", "datatype")}
                self.datatype_factory = DataTypeFactory()
                orm_models = get_resource_models_for_adapter()["by-class"]
                self.graphs = {
                    str(model.graphid): model for model in orm_models.values()
                }
                self.definitions = {}

                for _, model in orm_models.items():
                    model_name = model._model_name
                    self.definitions[model_name] = {
                        "model_name": model_name,
                        "model_class_name": model.__name__,
                        "fields": {
                            "id": {"type": DataTypeNames.STRING, "multiple": False}
                        }
                    }
                    for field, info in model.__fields__.items():
                        self._process_field(model_name, field, info, model)
                        self.definitions[model_name]["fields"][field] = info
                        # AGPL Arches

                self.inited = True
            except Exception as exc:
                self.exc = exc
                raise exc

    def _process_field(self, model_name, field, info, model):
        typ = info["type"]
        if typ == DataTypeNames.SEMANTIC:
            for subfield, subinfo in info.get("children", {}).items():
                self._build_semantic(field, subfield, subinfo, model_name, model.__name__)
                self._process_field(model_name, subfield, subinfo, model)
        elif typ in (DataTypeNames.RESOURCE_INSTANCE, DataTypeNames.RESOURCE_INSTANCE_LIST):
            nodeid = info["nodeid"]
            self._build_related(nodeid, field, model_name)
            def _construct_resource(vs, nodeid, field, model_name, datatype_instance):
                graphs = self.related_nodes[nodeid]["relatable_graphs"]
                assert len(graphs) == 1, f"Could not determine a unique type for this subgraph {field} of {model_name}"
                model = self.graphs[graphs[0]]
                resources = [_build_resource(model, **v) for v in vs]
                return resources

            self.remapped[(model_name, field)] = partial(
                lambda vs, nodeid: _construct_resource(vs, nodeid, field, model_name, None),
                nodeid=nodeid
            )
        elif typ in (DataTypeNames.CONCEPT, DataTypeNames.CONCEPT_LIST):
            nodeid = info["nodeid"]
            collection = Concept().get_child_collections(models.Node.objects.get(nodeid=nodeid).config["rdmCollection"])
            print(collection)
            self.collections[nodeid] = {
                "forward": {f"{string_to_enum(field)}.{string_to_enum(label[1])}": label[2] for label in collection},
                "back": {label[2]: string_to_enum(label[1]) for label in collection}
            }
            if typ == DataTypeNames.CONCEPT_LIST:
                self.remapped[(model_name, field)] = partial(
                    lambda vs, nodeid: list(map(self.collections[nodeid]["forward"].get, map(str, vs))),
                    nodeid=nodeid
                )
                self.demapped[(model_name, field)] = partial(
                    lambda vs, nodeid: list(map(self.collections[nodeid]["back"].get, map(str, vs))),
                    nodeid=nodeid
                )
            else:
                self.remapped[(model_name, field)] = partial(
                    lambda v, nodeid: self.collections[nodeid]["forward"][str(v)],
                    nodeid=nodeid
                )
                self.demapped[(model_name, field)] = partial(
                    lambda v, nodeid: self.collections[nodeid]["back"][str(v)],
                    nodeid=nodeid
                )

    def to_graphene_mut(self, info, field, model_class_name):
        typ = info["type"]
        if typ == DataTypeNames.SEMANTIC:
            semantic_type = (model_class_name, field)
            if semantic_type not in semantic_input_objects:
                args = []
                semantic_input_objects[semantic_type] = None # empty semantic fields are not useful
                if semantic_type in self.semantic_nodes:
                    semantic_detail = self.semantic_nodes[semantic_type]
                    for subfield, subinfo in semantic_detail["fields"]:
                        data_type = data_types.to_graphene_mut(subinfo, subfield, semantic_detail["model_class_name"])
                        if data_type:
                            args.append((subfield, data_type))
                    if args:
                        InputObjectType = type(
                            f"{model_class_name}{string_to_enum(field)}Input",
                            (graphene.InputObjectType,),
                            {
                                subfield: typ for subfield, typ in args
                            }
                        )
                        semantic_input_objects[semantic_type] = InputObjectType
            if semantic_input_objects[semantic_type]:
                return graphene.Argument(graphene.List(semantic_input_objects[semantic_type]) if info["multiple"] else semantic_input_objects[semantic_type])
            return None
        if typ in (DataTypeNames.STRING, DataTypeNames.DATE):
            graphene_type = graphene.String()
        elif typ == DataTypeNames.BOOLEAN:
            graphene_type = graphene.Boolean()
        elif typ == DataTypeNames.NUMBER:
            graphene_type = graphene.Float() # No distinct int type
        else:
            # RMV
            graphene_type = graphene.String if info["multiple"] else graphene.String()
        #elif isinstance(typ, str):
        #    return graphene.List(graphene.String())

        if typ in (DataTypeNames.CONCEPT, DataTypeNames.CONCEPT_LIST):
            collection = self.collections[info["nodeid"]]
            # We lose the conceptid here, so cannot spot duplicates, but the idea is
            # to restrict transfer to being human-readable.
            pairs = {}
            for n, value in enumerate(collection["back"].values()):
                pairs[value] = (value, n)
            if len(pairs) != len(collection["back"]):
                logging.warning(f"WARNING: duplicate enum entries for {field}")
            if not pairs:
                logging.warning(f"WARNING: no enum entries for {field}")
                return None
            raw_type = graphene.Enum(string_to_enum(field), list(pairs.values()))

            return graphene.Argument(graphene.List(raw_type) if typ == DataTypeNames.CONCEPT_LIST else raw_type)
        elif typ in (DataTypeNames.RESOURCE_INSTANCE, DataTypeNames.RESOURCE_INSTANCE_LIST):
            allowed_graphs = [str(wkrm.graphid) for wkrm in WELL_KNOWN_RESOURCE_MODELS]
            graphs = [
                graph for graph in self.related_nodes[info["nodeid"]]["relatable_graphs"]
                if graph in allowed_graphs
            ]
            logging.error("%s]", str(graphs))
            if len(graphs) == 0:
                logging.warning("Relations must relate a graph that is well-known")
                return None
            if len(graphs) == 1:
                graph = graphs[0]
                return graphene.Argument(graphene.List(lambda: _resource_model_inputs[self.graphs[graph].__name__]))
            else:
                union = type(
                    f"{model_class_name}{string_to_enum(field)}UnionInputType",
                    (graphene.InputObjectType,),
                    {
                        self.graphs[graph].__name__: graphene.List(lambda: _resource_model_inputs[self.graphs[graph].__name__]) for graph in graphs
                    }
                )
                return graphene.Argument(union)
        elif typ == DataTypeNames.GEOJSON_FEATURE_COLLECTION:
            graphene_type = graphene.JSONString()
        elif typ == DataTypeNames.EDTF:
            graphene_type = graphene.String()
        elif typ == DataTypeNames.URL:
            graphene_type = graphene.String()
        elif typ == DataTypeNames.FILE_LIST:
            return graphene.List(graphene.String)
        elif typ == DataTypeNames.USER:
            return graphene.Argument(graphene.List(UserInputType) if info["multiple"] else UserInputType)
        return graphene.List(graphene_type) if info["multiple"] else graphene_type

    def to_graphene(self, info, field, model_class_name):
        typ = info["type"]
        if typ == DataTypeNames.SEMANTIC:
            semantic_type = (model_class_name, field)
            if semantic_type not in semantic_schema_objects:
                fields = []
                semantic_schema_objects[semantic_type] = None # empty semantic fields are not useful
                if semantic_type in self.semantic_nodes:
                    semantic_detail = self.semantic_nodes[semantic_type]
                    for subfield, subinfo in semantic_detail["fields"]:
                        data_type = data_types.to_graphene(subinfo, subfield, semantic_detail["model_class_name"])
                        if data_type:
                            fields.append((subfield, data_type))
                    if fields:
                        SchemaType = type(
                            f"{model_class_name}{string_to_enum(field)}",
                            (graphene.ObjectType,),
                            {
                                subfield: typ for subfield, typ in fields
                            }
                        )
                        semantic_schema_objects[semantic_type] = SchemaType
            if semantic_schema_objects[semantic_type]:
                return graphene.List(semantic_schema_objects[semantic_type]) if info["multiple"] else graphene.Field(semantic_schema_objects[semantic_type])
            return None
        if typ in (DataTypeNames.STRING, DataTypeNames.DATE):
            graphene_type = graphene.String()
        elif typ == DataTypeNames.BOOLEAN:
            graphene_type = graphene.Boolean()
        elif typ == DataTypeNames.NUMBER:
            graphene_type = graphene.Float() # No distinct int type
        #elif isinstance(typ, str):
        #    return graphene.List(lambda: _resource_model_schemas[typ])

        if typ in (DataTypeNames.CONCEPT, DataTypeNames.CONCEPT_LIST):
            collection = self.collections[info["nodeid"]]
            # We lose the conceptid here, so cannot spot duplicates, but the idea is
            # to restrict transfer to being human-readable.
            pairs = {}
            for n, value in enumerate(collection["back"].values()):
                pairs[value] = (value, n)
            if len(pairs) != len(collection["back"]):
                logging.warning(f"WARNING: duplicate enum entries for {field}")
            if not pairs:
                logging.warning(f"WARNING: no enum entries for {field}")
                return None
            raw_type = graphene.Enum(string_to_enum(field), list(pairs.values()))

            return graphene.List(raw_type) if typ == DataTypeNames.CONCEPT_LIST else graphene.Field(raw_type)
        elif typ in (DataTypeNames.RESOURCE_INSTANCE, DataTypeNames.RESOURCE_INSTANCE_LIST):
            graphs = self.related_nodes[info["nodeid"]]["relatable_graphs"]
            if len(graphs) == 0:
                logging.warning("Relations must relate a graph that is well-known")
                return None
            if len(graphs) == 1:
                graph = graphs[0]
                return graphene.List(lambda: _resource_model_schemas[self.graphs[graph].__name__])
            else:
                def _make_union(graphs):
                    union = type(
                        f"{model_class_name}{string_to_enum(field)}Union",
                        (graphene.Union,),
                        {
                            "Meta": {"types": tuple({_resource_model_schemas[self.graphs[graph].__name__] for graph in graphs})},
                            "resolve_type": lambda cls, instance, info=None: _resource_model_schemas[cls._model_class_name]
                        }
                    )
                    return union
                return graphene.List(partial(_make_union, graphs))
        elif typ == DataTypeNames.GEOJSON_FEATURE_COLLECTION:
            graphene_type = graphene.JSONString()
        elif typ == DataTypeNames.EDTF:
            graphene_type = graphene.String()
        elif typ == DataTypeNames.URL:
            graphene_type = graphene.String()
        elif typ == DataTypeNames.FILE_LIST:
            return graphene.List(graphene.String)
        elif typ == DataTypeNames.USER:
            return graphene.List(UserType) if info["multiple"] else graphene.Field(UserType)
        else:
            # RMV
            graphene_type = graphene.String if info["multiple"] else graphene.String()
        return graphene.List(graphene_type) if info["multiple"] else graphene_type

data_types = DataTypes()

# Do synchronous data retrieval of "constants". After this, we assume they are available.
thread = threading.Thread(target=data_types.init)
thread.start()
thread.join()
if data_types.exc:
    raise data_types.exc

semantic_input_objects = {}
semantic_schema_objects = {}

_resource_model_mappers = {
    wkrm.model_class_name: {
        field: partial(data_types.demap, wkrm.model_name, field)
        for field, info in data_types.definitions[wkrm.model_name]["fields"].items()
    }
    for wkrm in WELL_KNOWN_RESOURCE_MODELS
    if wkrm.model_name in data_types.definitions
}
_resource_model_schemas = {
    wkrm.model_class_name: type(
        wkrm.model_class_name,
        (graphene.ObjectType,),
        {
            field: arg for field, arg in
            {
                field: data_types.to_graphene(info, field, wkrm.model_class_name)
                for field, info in data_types.definitions[wkrm.model_name]["fields"].items()
            }.items()
            if arg
        }
    )
    for wkrm in WELL_KNOWN_RESOURCE_MODELS
    if wkrm.model_name in data_types.definitions
}
_resource_model_inputs = {
    wkrm.model_class_name: type(
        f"{wkrm.model_class_name}Input",
        (graphene.InputObjectType,),
        {
            field: arg for field, arg in
            {
                field: data_types.to_graphene_mut(info, field, wkrm.model_class_name)
                for field, info in data_types.definitions[wkrm.model_name]["fields"].items()
            }.items()
            if arg
        }
    )
    for wkrm in WELL_KNOWN_RESOURCE_MODELS
    if wkrm.model_name in data_types.definitions
}

class UnavailableResourceInstance:
    id = "[UNAVAILABLE]"

class ResourceInstanceLoader(DataLoader):
    async def batch_load_fn(self, keys):
        # FIXME: proper authorization integration
        if not ALLOW_ANONYMOUS and not context.data["user"].is_superuser:
            return [UnavailableResourceInstance for _ in keys]
        # Here we call a function to return a user for each key in keys
        out = list(await sync_to_async(self._batch_load_fn_real)(keys))
        return out

    def _batch_load_fn_real(self, keys):
        ret = []
        for key in keys:
            try:
                resource = attempt_well_known_resource_model(key)
            except arches.app.models.resource.Resource.DoesNotExist:
                ret.append(None) # must send back the same number
            else:
                ret.append(resource)

        group = []
        for wkrm in ret:
            if wkrm:
                group.append(
                    {field: mapper(getattr(wkrm, field, None)) for field, mapper in _resource_model_mappers[wkrm._wkrm.model_class_name].items()}
                )
            else:
                group.append(None)
        return group


_name_map = {
    snake(wkrm.model_class_name): wkrm.model_class_name
    for wkrm in WELL_KNOWN_RESOURCE_MODELS
}

async def resolver(field, root, _, info, **kwargs):
    only_one = False
    try:
        model_class_name = _name_map[field]
    except KeyError:
        if field.startswith("get_"):
            all_ids = [str(kwargs["id"])]
            only_one = True
        elif field.startswith("search_"):
            model_class_name = _name_map[field[7:]]
            model_class = get_well_known_resource_model_by_class_name(model_class_name)
            all_ids, _ = await sync_to_async(model_class.search)(**kwargs)
    else:
        model_class = get_well_known_resource_model_by_class_name(model_class_name)
        models = await sync_to_async(model_class.all_ids)()
        all_ids = [str(idx) for idx in models]
    ri_loader = get_loader("ResourceInstance")
    if only_one:
        if len(all_ids) != 1:
            raise RuntimeError("Only one ID expected")
        return (await ri_loader.load_many(all_ids))[0]
    return await ri_loader.load_many(all_ids)

_full_resource_query_methods = {}
for wkrm in WELL_KNOWN_RESOURCE_MODELS:
    if wkrm.model_class_name in _resource_model_schemas:
        _full_resource_query_methods[snake(wkrm.model_class_name)] = graphene.List(_resource_model_schemas[wkrm.model_class_name])
        _full_resource_query_methods[f"get_{snake(wkrm.model_class_name)}"] = graphene.Field(_resource_model_schemas[wkrm.model_class_name], id=graphene.UUID(required=True))
        _full_resource_query_methods[f"search_{snake(wkrm.model_class_name)}"] = graphene.List(_resource_model_schemas[wkrm.model_class_name], text=graphene.String(), fields=graphene.List(graphene.String))
        _full_resource_query_methods[f"list_{snake(wkrm.model_class_name)}"] = graphene.List(_resource_model_schemas[wkrm.model_class_name])

ResourceQuery = type(
    "ResourceQuery",
    (graphene.ObjectType,),
    _full_resource_query_methods,
    default_resolver=resolver
)

class FileUploadMutation(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        return FileUploadMutation(ok=True)


class Mutation(graphene.ObjectType):
    upload_file = FileUploadMutation.Field()

async def mutate_bulk_create(parent, info, mutation, resource_cls, field_sets, do_index=False):
    # FIXME: proper authorization
    if not ALLOW_ANONYMOUS and not context.data["user"].is_superuser:
        return {
            snake(resource_cls.__name__): None,
            "ok": False
        }

    field_sets = [{field: data_types.remap(resource_cls.__name__, field, value) for field, value in field_set.items()} for field_set in field_sets]
    resources = await sync_to_async(resource_cls.create_bulk)(field_sets, do_index=do_index)
    ok = True
    kwargs = {
        snake(resource_cls.__name__) + "s": resources,
        "ok": ok
    }
    return mutation(**kwargs)

async def mutate_create(parent, info, mutation, resource_cls, field_set, do_index=True):
    # FIXME: proper authorization
    if not ALLOW_ANONYMOUS and not context.data["user"].is_superuser:
        return {
            snake(resource_cls.__name__): None,
            "ok": False
        }

    resource = _build_resource(resource_cls, **field_set)
    await sync_to_async(resource.to_resource)()
    if do_index:
        await sync_to_async(resource.index)()
    ok = True
    kwargs = {
        snake(resource_cls.__name__): resource,
        "ok": ok
    }
    return mutation(**kwargs)

def _build_resource(resource_cls, **kwargs):
    kwargs = {field: data_types.remap(resource_cls.__name__, field, value) for field, value in kwargs.items()}
    resource = resource_cls.build(**kwargs)
    return resource

async def mutate_delete(parent, info, mutation, resource_cls, id):
    # FIXME: proper authorization
    if not ALLOW_ANONYMOUS and not context.data["user"].is_superuser:
        return {
            snake(resource_cls.__name__): None,
            "ok": False
        }

    resource = await sync_to_async(resource_cls.find)(id)
    await sync_to_async(resource.delete)()
    ok = True
    kwargs = {
        "ok": ok
    }
    return mutation(**kwargs)

_full_resource_mutation_methods = {}
for wkrm in WELL_KNOWN_RESOURCE_MODELS:
    if wkrm.model_name not in data_types.definitions:
        continue
    ResourceSchema = _resource_model_schemas[wkrm.model_class_name]
    ResourceInputObjectType = _resource_model_inputs[wkrm.model_class_name]
    mutations = {}
    mutations["BulkCreateResource"] = type(
        f"BulkCreate{wkrm.model_class_name}",
        (graphene.Mutation,),
        {
            "ok": graphene.Boolean(),
            snake(wkrm.model_class_name) + "s": graphene.Field(graphene.List(ResourceSchema)),
            "mutate": partial(
                lambda *args, mutations=None, **kwargs: mutate_bulk_create(*args, mutation=mutations["BulkCreateResource"], **kwargs),
                resource_cls=data_types.graphs[wkrm.graphid],
                mutations=mutations
            )
        },
        arguments={
            "field_sets": graphene.List(ResourceInputObjectType),
            "do_index": graphene.Boolean(required=False, default_value=True)
        }
    )
    mutations["CreateResource"] = type(
        f"Create{wkrm.model_class_name}",
        (graphene.Mutation,),
        {
            "ok": graphene.Boolean(),
            snake(wkrm.model_class_name): graphene.Field(ResourceSchema),
            "mutate": partial(
                lambda *args, mutations=None, **kwargs: mutate_create(*args, mutation=mutations["CreateResource"], **kwargs),
                resource_cls=data_types.graphs[wkrm.graphid],
                mutations=mutations
            )
        },
        arguments={
            "field_set": graphene.Argument(ResourceInputObjectType),
            "do_index": graphene.Boolean(required=False, default_value=True)
        }
    )
    mutations["DeleteResource"] = type(
        f"Delete{wkrm.model_class_name}",
        (graphene.Mutation,),
        {
            "ok": graphene.Boolean(),
            "mutate": partial(
                lambda *args, mutations=None, **kwargs: mutate_delete(*args, mutation=mutations["DeleteResource"], **kwargs),
                resource_cls=data_types.graphs[wkrm.graphid],
                mutations=mutations
            )
        },
        arguments={
            "id": graphene.UUID()
        }
    )
    _full_resource_mutation_methods.update({
        f"create_{snake(wkrm.model_class_name)}": mutations["CreateResource"].Field(),
        f"bulk_create_{snake(wkrm.model_class_name)}": mutations["BulkCreateResource"].Field(),
        f"delete_{snake(wkrm.model_class_name)}": mutations["DeleteResource"].Field()
    })

FullResourceMutation = type(
    "FullResourceMutation",
    (Mutation,),
    _full_resource_mutation_methods,
)

resources_schema = graphene.Schema(query=ResourceQuery, mutation=FullResourceMutation)

_LOADERS = {
    "ResourceInstance": ResourceInstanceLoader
}
def get_loader(loader):
    """Make sure we have fresh loaders per request."""
    context.data.setdefault("loaders", {})
    loaders = context.data["loaders"]
    if loader not in loaders:
        loaders[loader] = _LOADERS[loader]()
    return loaders[loader]
