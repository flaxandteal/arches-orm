from __future__ import annotations

import logging
from uuid import UUID
from enum import Enum
from typing import Any, Generator, Callable, Literal
from inspect import isgenerator, isgeneratorfunction
from functools import partial, wraps
from contextlib import contextmanager
from contextvars import ContextVar
from abc import ABC, abstractmethod

from rdflib.term import Node

from .view_models._base import ResourceInstanceViewModel
from .view_models.concepts import ConceptValueViewModel

logger = logging.getLogger(__name__)

class Adapter(ABC):
    config: dict[str, Any]
    _context: ContextVar[dict[str, Any] | None]
    _singleton: Adapter | None = None

    def __init__(self, key):
        self.config = {}
        self._context = ContextVar(key)

    def __init_subclass__(cls):
        ADAPTER_MANAGER.register_adapter(cls)

    def __str__(self):
        return self.key

    def __repr__(self):
        return f"<AORA:{self.key}>"

    @property
    @abstractmethod
    def key(self):
        ...

    def set_context_free(self):
        self._context.set(None)

    def get_rdm(self):
        from .collection import ReferenceDataManager
        return ReferenceDataManager(self)

    @abstractmethod
    def retrieve_concept_value(self, concept_id: str | UUID) -> ConceptValueViewModel:
        ...

    @abstractmethod
    def make_concept(self, concept_id: str | UUID, values: dict[UUID, tuple[str, str, Node]], children: list[UUID] | None) -> ConceptValueViewModel:
        ...

    @abstractmethod
    def get_collection(self, collection_id: str | UUID) -> type[Enum]:
        ...

    @abstractmethod
    def get_collections_by_label(self, label: str, pref_label_only: bool=False) -> list[type[Enum]]:
        ...

    @abstractmethod
    def get_concepts_by_label(self, label: str, pref_label_only: bool=False) -> list[ConceptValueViewModel]:
        ...

    @abstractmethod
    def derive_collection(self, collection_id: str | UUID, include: list[UUID] | None, exclude: list[UUID] | None, language: str | None=None) -> type[Enum]:
        """Note that include and exclude should be lists of concept, not value, IDs."""
        ...

    @abstractmethod
    def load_from_id(self, resource_id: str, from_prefetch: Callable[[str], Any] | None=None, lazy: bool=False) -> ResourceInstanceViewModel:
        ...

    def get_context(self):
        return self._context

    @contextmanager
    def context_free(self) -> Generator[ContextVar[dict[str, Any] | None], None, None]:
        with self.context(_ctx=None) as cvar:
            yield cvar

    @contextmanager
    def context(self, _ctx: dict[str, Any] | ContextVar | None | Literal[False]=False, _override=False, **kwargs: dict[str, Any]) -> Generator[ContextVar[dict[str, Any] | None], None, None]:
        # We use _ctx to be False to show unpassed, as None is a valid value for the contextvar
        try:
            context = self._context.get()
        except LookupError:
            ...
        else:
            # Allows nesting, provided the context does not change.
            if isinstance(_ctx, ContextVar):
                new_ctx = _ctx.get()
            else:
                new_ctx = _ctx
            if new_ctx is not context:
                if context is None:
                    # This is OK, as we can provide _more_ context, if not less.
                    pass
                elif not _override:
                    raise RuntimeError("Context is already set")

        if _ctx is False:
            _ctx = kwargs
        if isinstance(_ctx, ContextVar):
            old_ctx = self._context
            self._context = _ctx
            try:
                yield self._context
            finally:
                self._context = old_ctx
        else:
            tok = self._context.set(_ctx)
            try:
                yield self._context
            finally:
                self._context.reset(tok)

class PseudoNodeAdapterMixin:
    def from_pseudo_node_wrapper(self, wrapper, from_prefetch=None):
        from .pseudo_node.value_list import ValueList
        # TODO: this should probably be merged into the Adapter structure
        from .wkrm import get_resource_models_for_adapter
        resource_models = get_resource_models_for_adapter(self.key)["by-graph-id"]
        # Standardize
        graphid = UUID(wrapper._.graphid) if not isinstance(wrapper._.graphid, UUID) else wrapper._.graphid
        if graphid not in resource_models:
            raise RuntimeError(f"Adapter {self.key} does not have graph {graphid}")
        wkri = resource_models[graphid]()
        wkri._._values = ValueList(values=wrapper._._values._values, wrapper=wkri._, related_prefetch=from_prefetch)
        return wkri


class AdapterManager:
    default_adapter = None

    def __init__(self):
        self.adapters = {}

    def register_adapter(self, adapter_cls, key=None):
        if key is None:
            key = adapter_cls.key
        if key in self.adapters:
            raise RuntimeError("Cannot register same adapter multiple times")
        if len(self.adapters) and not self.default_adapter:
            raise RuntimeError(
                "Must set a default adapter, if registering multiple in one process"
            )
        adapter = adapter_cls(key=key)
        adapter_cls._singleton = adapter
        self.adapters[key] = adapter

    def set_default_adapter(self, default_adapter):
        self.default_adapter = default_adapter

    def get_adapter(self, key=None):
        if not self.adapters:
            raise RuntimeError(
                "Must have at least one adapter available, "
                "did you mean to import an adapter module?"
            )
        if key is not None:
            adapter = self.adapters[key]
        elif len(self.adapters) > 1:
            if not self.default_adapter:
                raise RuntimeError(
                    "You have imported multiple adapters, "
                    "you must set an explicit default."
                )
            adapter = self.adapters[self.default_adapter]
        else:
            adapter = list(self.adapters.values())[0]
        return adapter

def context_free(arg: Callable[[Any], Any] | str) -> Callable[[Any], Any]:
    if callable(arg):
        return context(None, None)(arg)
    return context(None, arg)

def context(ctx: dict | None, adapter_key: str | None=None) -> Callable[[Any], Any]:
    def wrapper(adapter_key: str | None, f: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @wraps(f)
        def _g(*args, **kwargs):
            adapter = get_adapter(adapter_key)
            with adapter.context(_ctx=ctx, _override=True) as _:
                yield from f(*args, **kwargs)

        @wraps(f)
        def _f(*args, **kwargs):
            adapter = get_adapter(adapter_key)
            with adapter.context(_ctx=ctx, _override=True) as _:
                return f(*args, **kwargs)
        return _g if isgenerator(f) or isgeneratorfunction(f) else _f

    return partial(wrapper, adapter_key)

@contextmanager
def admin(adapter_key: str | None=None):
    with get_adapter(adapter_key).context(None, _override=True) as cvar:
        yield cvar

def admin_everywhere(key=None):
    get_adapter(key=key).set_context_free()
    logger.warning(
        "ARCHES ORM ADMINISTRATION MODE ON: use for debugging only, "
        "otherwise use the `context_free` or `context` decorator/with statement to "
        "achieve this result safely."
    )

ADAPTER_MANAGER = AdapterManager()
get_adapter = ADAPTER_MANAGER.get_adapter
