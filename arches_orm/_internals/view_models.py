from typing import Union
import uuid
from functools import lru_cache
from django.contrib.auth.models import User
from arches.app.models.models import Node
from arches.app.datatypes.datatypes import StringDataType
from arches.app.datatypes.concept_types import ConceptDataType
from arches.app.datatypes.base import BaseDataType
from arches.app.models.tile import Tile


class UserViewModel(str):
    """Wraps a user, so that a Django User can be obtained.

    To access the actual user, use `.user`.
    """

    _tile: Tile
    _nodeid: uuid.UUID
    _user_datatype: BaseDataType

    def __new__(cls, tile, node, user_datatype):
        display_value = user_datatype.get_display_value(
            tile,
            Node(nodeid=node.nodeid),
        )
        mystr = super(UserViewModel, cls).__new__(cls, display_value)
        cls._tile = tile
        cls._nodeid = node.nodeid
        cls._user_datatype = user_datatype
        return mystr

    @property
    def user(self):
        user = User.objects.get(pk=int(self._tile.data[str(self._nodeid)]))
        return user


class StringViewModel(str):
    """Wraps a string, allowing language translation.

    Subclasses str, but also allows `.lang("zh")`, etc. to re-translate.
    """

    _tile: Tile
    _nodeid: uuid.UUID
    _string_datatype: StringDataType

    def __new__(cls, tile, node, string_datatype, language=None):
        display_value = string_datatype.get_display_value(
            tile, Node(nodeid=node.nodeid), language=language
        )
        mystr = super(StringViewModel, cls).__new__(cls, display_value)
        cls._tile = tile
        cls._nodeid = node.nodeid
        cls._string_datatype = string_datatype
        return mystr

    def lang(self, language):
        return self._string_datatype.get_display_value(
            self._tile, Node(nodeid=self._nodeid), language=language
        )


class ConceptValueViewModel(str):
    """Wraps a concept, allowing interrogation.

    Subclasses str, so it can be handled like a string enum, but keeps
    the `.value`, `.lang` and `.text` properties cached, so you can
    find out more.
    """

    _concept_value_id: uuid.UUID
    _concept_datatype: ConceptDataType

    def __new__(cls, concept_value_id: Union[str, uuid.UUID], concept_datatype):
        _concept_value_id: uuid.UUID = (
            concept_value_id
            if isinstance(concept_value_id, uuid.UUID)
            else uuid.UUID(concept_value_id)
        )
        mystr = super(ConceptValueViewModel, cls).__new__(cls, str(_concept_value_id))
        mystr._concept_value_id = _concept_value_id
        mystr._concept_datatype = concept_datatype
        return mystr

    @property
    @lru_cache
    def conceptid(self):
        return self.value.concept_id

    @property
    @lru_cache
    def concept(self):
        return self.value.concept

    @property
    @lru_cache
    def value(self):
        return self._concept_datatype.get_value(self._concept_value_id)

    @property
    @lru_cache
    def text(self):
        return self.value.value

    @property
    @lru_cache
    def lang(self):
        return self.value.language

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"{self.value.concept_id}>{self._concept_value_id}[{self.text}]"
