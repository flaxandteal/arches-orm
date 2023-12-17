class Adapter:
    def __init_subclass__(cls):
        ADAPTER_MANAGER.register_adapter(cls)


class AdapterManager:
    default_adapter = None

    def __init__(self):
        self.adapters = {}

    def register_adapter(self, adapter_cls):
        adapter = adapter_cls()
        key = str(adapter)
        if key in self.adapters:
            raise RuntimeError("Cannot register same adapter multiple times")
        if len(self.adapters) and not self.default_adapter:
            raise RuntimeError(
                "Must set a default adapter, if registering multiple in one process"
            )
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


ADAPTER_MANAGER = AdapterManager()
get_adapter = ADAPTER_MANAGER.get_adapter
