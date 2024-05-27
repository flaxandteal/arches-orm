class ViewModel:
    _parent_pseudo_node = None

class ResourceModelViewModel(type, ViewModel):
    """Wraps a resource model."""

    def __getattr__(self, key):
        return getattr(self._, key)

    def __setattr__(self, key, value):
        raise NotImplementedError()

class ResourceInstanceViewModel(ViewModel, metaclass=ResourceModelViewModel):
    """Wraps a resource instance."""

    @property
    def id(self):
        return self._.id

    def describe(self):
        return {
            "name": self._._name,
            "description": self._._description,
        }

    def delete(self, *args, **kwargs):
        return self._.delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self._.save(*args, **kwargs)
        return self

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        cls._(obj, *args, **kwargs)
        return obj

    def __str__(self):
        """Convert to string."""
        return self._.to_string()

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __getattr__(self, key):
        if key.startswith("__"):
            return super().__getattr__(key)
        return self._.get_orm_attribute(key)

    def __setitem__(self, key, value):
        return self.__setattr__(key, value)

    def __setattr__(self, key, value):
        """Set Python values for nodes attributes."""

        if key in ("_",):
            return super().__setattr__(key, value)
        return self._.set_orm_attribute(key, value)

    def __eq__(self, other):
        return (
            self.id
            and other.id
            and self.id == other.id
            and self.__class__ == other.__class__
        )

    def _set_class(self, cls):
        super().__setattr__("__class__", cls)

class UnavailableViewModel(ViewModel):
    def __str__(self):
        """Convert to string."""
        return "(unavailable)"
