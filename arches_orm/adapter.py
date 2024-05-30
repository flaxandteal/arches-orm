import logging
from typing import Any, Generator, Callable, Literal
from inspect import isgenerator, isgeneratorfunction
from functools import partial, wraps
from contextlib import contextmanager
from contextvars import ContextVar

_ADMINISTRATION_MODE: bool = False

logger = logging.getLogger(__name__)

class Adapter:
    config: dict[str, Any]
    _context: ContextVar[dict[str, Any] | None]

    def __init__(self, key):
        self.config = {}
        self._context = ContextVar(key)

    def __init_subclass__(cls):
        ADAPTER_MANAGER.register_adapter(cls)

    def set_context_free(self):
        self._context.set(None)

    def get_context(self):
        if _ADMINISTRATION_MODE:
            try:
                self._context.get()
            except LookupError:
                self._context.set(None)

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

def admin_everywhere():
    _ADMINISTRATION_MODE = True
    logger.warning(
        "ARCHES ORM ADMINISTRATION MODE ON: use for debugging only, "
        "otherwise use the `context_free` or `context` decorator/with statement to "
        "achieve this result safely."
    )

ADAPTER_MANAGER = AdapterManager()
get_adapter = ADAPTER_MANAGER.get_adapter
