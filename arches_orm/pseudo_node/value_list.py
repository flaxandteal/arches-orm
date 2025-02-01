from collections import UserDict

class ValueList(UserDict):
    def __init__(self, values, wrapper, related_prefetch):
        self._wrapper = wrapper
        self._related_prefetch = related_prefetch
        self._values = values

    @property
    def data(self):
        return {
            k: v for k, v in self._values.items() if v is not False
        }

    def setdefault(self, key, value):
        # Gives us a chance to lazy-load
        self._get(key, value, raise_error=False)
        self._values.setdefault(key, value)

    def __setitem__(self, key, value):
        self._values[key] = value

    def __getitem__(self, key):
        result = self._values[key]
        return self._get(key, default=result, raise_error=True)

    def _get(self, key, default=None, raise_error=False):
        result = self._values.get(key, default)
        if result is False:
            if self._wrapper.resource:
                # Will KeyError if we do not have it.
                node = self._wrapper._nodes[key]
                ng = self._wrapper._ensure_nodegroup(
                    self._values,
                    node.nodegroup_id,
                    self._wrapper._node_objects(),
                    self._wrapper._nodegroup_objects(),
                    self._wrapper._edges(),
                    self._wrapper.resource,
                    related_prefetch=self._related_prefetch,
                    wkri=self._wrapper.view_model_inst,
                )
                self._values.update(ng)
            else:
                del self._values[key]
        if raise_error:
            return self.data[key]
        else:
            return self.data.get(key, default)

