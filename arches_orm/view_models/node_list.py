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

    def pop(self):
        item = self.nodelist.pop()
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
