import re
from collections.abc import Iterable
import uuid
from django.contrib.auth.models import User
from arches.app.models.concept import Concept
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.search.elasticsearch_dsl_builder import Bool, Ids, Match, Nested, SimpleQueryString, QueryString, Terms, Term
from arches.app.search.components.term_filter import _get_child_concepts
from arches.app.utils.permission_backend import get_nodegroups_by_perm
from arches_orm.errors import WKRMPermissionDenied


from dataclasses import dataclass
from typing import Literal, Any

class NodegroupPermissionMixin:
    _permitted_nodegroups: list[str] | None = None

    def override_permitted_nodegroups(self, permitted_nodegroups: list[str]) -> None:
        self._permitted_nodegroups = permitted_nodegroups

    def get_permitted_nodegroups(self, user: User | None=None) -> list[str]:
        if self._permitted_nodegroups is not None:
            return self._permitted_nodegroups
        return get_nodegroups_by_perm(user, "models.read_nodegroup") # type: ignore

class BaseFilter(NodegroupPermissionMixin):
    inverted: bool
    include_provisional: bool | Literal["only provisional"]
    ignore_nodegroup_permissions: bool

    def __init__(self, inverted: bool=False, include_provisional: bool | Literal["only provisional"]=False, ignore_nodegroup_permissions: bool=False):
        self.inverted = inverted
        self.include_provisional = include_provisional
        self.ignore_nodegroup_permissions = ignore_nodegroup_permissions

class BaseStringFilter(BaseFilter):
    language: str
    value: str

    def __init__(self, value: str, language: str | None=None, **kwargs: dict[str, Any]):
        super().__init__(**kwargs) # type: ignore

        self.value = value
        self.language = language or "*"

    def build(self, filt=None):
        if filt is None:
            filt = Bool()

        string_filter = Bool()
        if self.include_provisional is False:
            string_filter.must_not(Match(field="strings.provisional", query="true", type="phrase"))
        elif self.include_provisional == "only provisional":
            string_filter.must_not(Match(field="strings.provisional", query="false", type="phrase"))

        if self.ignore_nodegroup_permissions is not True:
            string_filter.filter(Terms(field="strings.nodegroup_id", terms=self.get_permitted_nodegroups()))
        nested_string_filter = Nested(path="strings", query=string_filter)
        if self.inverted:
            filt.must_not(nested_string_filter)
        else:
            filt.must(nested_string_filter)

        return filt

@dataclass
class StringFilter(BaseStringFilter):
    def build(self, filt=None):
        if filt is None:
            filt = Bool()

        filt.must(Match(field="strings.string", query=self.value, type="phrase"))
        return super().build(filt)

@dataclass
class TermFilter(BaseStringFilter):
    def build(self, filt=None):
        if filt is None:
            filt = Bool()

        value = self.value

        try:
            uuid.UUID(str(value))
            filt.must(Ids(ids=value))
        except:
            if self.language != "*":
                filt.must(Match(field="strings.language", query=self.language, type="phrase_prefix"))
            exact_term = re.search('"(?P<search_string>.*)"', value)
            if exact_term:
                search_string = exact_term.group("search_string")
                filt.should(Term(field="strings.string.raw", term=search_string))
            elif "?" in value or "*" in value:
                reserved_chars = '+ - = && || > < ! ( ) { } [ ] ^ " ~ : /'.split(" ")
                for rc in reserved_chars:
                    value = value.replace(rc, f"\\{rc}")
                filt.must(QueryString(field="strings.string.folded", default_operator="AND", query=self.value))
            elif "|" in self.value or "+" in self.value:
                filt.must(SimpleQueryString(field="strings.string", operator="and", query=self.value))
            else:
                filt.should(Match(field="strings.string", query=self.value, type="phrase_prefix"))
                filt.should(Match(field="strings.string.folded", query=self.value, type="phrase_prefix"))

        return super().build(filt)

class ConceptFilter(BaseFilter):
    def __init__(self, value: str, language: str | None=None, **kwargs: dict[str, Any]):
        super().__init__(**kwargs) # type: ignore

        self.value = value

    def build(self, filt=None):
        if filt is None:
            filt = Bool()

        concept_ids = _get_child_concepts(self.value)
        conceptid_filter = Bool()
        conceptid_filter.filter(Terms(field="domains.conceptid", terms=concept_ids))
        if self.ignore_nodegroup_permissions is not True:
            conceptid_filter.filter(Terms(field="domains.nodegroup_id", terms=self.get_permitted_nodegroups()))

        if self.include_provisional is False:
            conceptid_filter.must_not(Match(field="domains.provisional", query="true", type="phrase"))
        elif self.include_provisional == "only provisional":
            conceptid_filter.must_not(Match(field="domains.provisional", query="false", type="phrase"))

        nested_conceptid_filter = Nested(path="domains", query=conceptid_filter)
        if self.inverted:
            filt.must_not(nested_conceptid_filter)
        else:
            filt.filter(nested_conceptid_filter)

        return filt

class SearchMixin:
    @classmethod
    def search(cls, text: str | list[str]=None, term: str | list[str]=None, concept: str | list[str]=None, fields=None, _total=None):
        """Search ES for resources of this model, and return as well-known resources."""

        if not cls ._can_read_graph():
            raise WKRMPermissionDenied()

        from arches.app.search.search_engine_factory import SearchEngineFactory
        from arches.app.views.search import RESOURCES_INDEX
        from arches.app.search.elasticsearch_dsl_builder import (
            Bool,
            Match,
            Query,
            Nested,
            Terms,
        )

        # AGPL Arches
        se = SearchEngineFactory().create()
        permitted_nodegroups = cls._permitted_nodegroups()
        permitted_nodegroups = [
            str(node.nodegroup_id)
            for key, node in cls._node_objects_by_alias().items()
            if (fields is None or key in fields) and (node.nodegroup_id is None or node.nodegroup_id in permitted_nodegroups)
        ]

        query = Query(se)
        fltr = Bool()

        if not isinstance(text, str) and isinstance(text, Iterable):
            text = [text]
        elif text is None:
            text = []
        if not isinstance(term, str) and isinstance(term, Iterable):
            term = [term]
        elif term is None:
            term = []
        if not isinstance(concept, str) and isinstance(concept, Iterable):
            concept = [concept]
        elif concept is None:
            concept = []

        language = cls._context_get("language")
        for cpt in concept:
            if hasattr(cpt, "conceptid"):
                cpt = cpt.conceptid
            ConceptFilter(str(cpt), language=language).build(fltr)
        for trm in term:
            TermFilter(str(trm), language=language).build(fltr)
        for txt in text:
            StringFilter(str(txt), language=language).build(fltr)

        query.add_query(fltr)
        query.min_score("0.01")

        query.include("resourceinstanceid")
        results = query.search(index=RESOURCES_INDEX, id=None)

        results = [
            hit["_source"]["resourceinstanceid"] for hit in results["hits"]["hits"]
        ]
        total_count = query.count(index=RESOURCES_INDEX)
        return results, total_count
