from collections import UserList
from ._base import (
    ViewModel,
)


class NodeListViewModel(UserList, ViewModel):
    def __init__(self, nodelist):
        self.nodelist = nodelist
        self._parent_pseudo_node = self.nodelist

    @property
    def data(self):
        return [node.value for node in self.nodelist]

    def append(self, item=None):
        value = self.nodelist.append(item)
        return value

    def extend(self, other):
        self.nodelist.extend(other)

    def sort(self, /, *args, **kwds):
        self.nodelist.sort(*args, **kwds)

    def reverse(self):
        self.nodelist.reverse()

    def clear(self):
        self.nodelist.clear()

    def remove(self, item):
        self.nodelist.remove(item)

    def pop(self, i=None):
        item = self.nodelist.pop(i)
        return item.value

    def insert(self, i, item):
        value = self.nodelist.insert(i, item)
        return value

    def __setitem__(self, i, item):
        self.nodelist[i] = item

    def __delitem__(self, i):
        del self.nodelist[i]

    def __iadd__(self, other):
        self.nodelist += other

def _traverse(cmpt, path):
    for ckey in path.split("."):
        if isinstance(cmpt, UserList):
            if len(cmpt) > 1:
                raise RuntimeError("Can only pull out a remapped key without a * if it has no >1 iterable in node hierarchy")
            elif len(cmpt) == 1:
                cmpt = cmpt[0]
            else:
                # FIXME: should this ever be hit?
                cmpt = cmpt.append()
        cmpt = getattr(cmpt, ckey)
    return cmpt

def _traverse_set(cmpt, path, item):
    if "." in path:
        path, final = path.split(".", -1)
        for ckey in path.split("."):
            if isinstance(cmpt, UserList):
                if len(cmpt) > 1:
                    raise RuntimeError("Can only pull out a remapped key without a * if it has no >1 iterable in node hierarchy")
                elif len(cmpt) == 1:
                    cmpt = cmpt[0]
                else:
                    cmpt = cmpt.append()
            cmpt = getattr(cmpt, ckey)
    else:
        final = path
    setattr(cmpt, final, item)

class RemappedNodeListViewModel(NodeListViewModel, ViewModel):
    def __init__(self, nodelist, path):
        self.nodelist = nodelist
        self._path = path
        self._parent_pseudo_node = self.nodelist

    @property
    def data(self):
        values = super().data
        return [_traverse(value, self._path) for value in values]

    def append(self, item=None):
        value = super().append(item=None)
        if item is not None:
            _traverse_set(value, self._path, item)
        return item

    def extend(self, other):
        raise NotImplementedError("Cannot apply operation to remapped list")

    def sort(self, /, *args, **kwds):
        self.data.sort(*args, **kwds)

    def remove(self, item):
        for real_item in self.nodelist:
            if _traverse(real_item, self._path) == item:
                self.nodelist.real_item(item)

    def pop(self):
        item = self.nodelist.pop()
        return _traverse(item.value, self._path)

    def insert(self, i, item):
        raise NotImplementedError("Cannot apply operation to remapped list")

    def __setitem__(self, i, item):
        _traverse_set(self.nodelist[i], self._path, item)

    def __iadd__(self, other):
        raise NotImplementedError("Cannot apply operation to remapped list")
