from __future__ import annotations

from enum import Enum
from typing import Union, Callable, Protocol, Any
import uuid
from functools import lru_cache
from collections import UserList
from collections.abc import Iterable
from arches_orm.utils import string_to_enum
from ._base import (
    ViewModel,
)

from typing import TypedDict, Dict, List
from uuid import UUID

DEFAULT_LANGUAGE = "en"

""" TYPING """
class DomainOptionText(TypedDict):
    en: str

class DomainOption(TypedDict):
    id: UUID
    text: DomainOptionText
    selected: bool

DomainOptions = List[DomainOption]

class DomainEnum(Enum):
    __original_name__: str = None
    __identifier__: str = None

_DOMAIN_ENUMS: dict[UUID, DomainEnum] = {}

def get_domain_enum(identifier: UUID):
    return _DOMAIN_ENUMS.get(identifier)

def make_domain_enum(name: str, domain: list[DomainValueViewModel], identifier: UUID | None, lang: str | None = None) -> DomainEnum:
    if identifier and (enum := get_domain_enum(identifier)):
        return enum
    values = dict()
    domain_values = dict()
    selected = None
    for entry in domain:
        values[entry.enum] = entry
        domain_values[entry.domain_value_id] = entry
        if entry.selected:
            selected = entry
    new_collection = DomainEnum(string_to_enum(name), values) # type: ignore
    setattr(new_collection, "__original_name__", name)
    setattr(new_collection, "__identifier__", identifier)
    setattr(new_collection, "__selected__", selected)
    setattr(new_collection, "__domain_values__", domain_values)
    _DOMAIN_ENUMS[identifier] = new_collection
    return new_collection


class DomainValue:
    _domain_id: UUID | None
    _domain_option: DomainOption | None
    _domain_cb: Callable[[UUID], type[Enum]]

    def __init__(self, domain_id: UUID):
        self._domain_id = domain_id

    @property
    def __domain__(self) -> type[Enum] | None:
        if (domain_enum := _DOMAIN_ENUMS.get(self._domain_id)):
            return domain_enum
        return None

""" VIEW MODELS """

class EmptyDomainValueViewModel(DomainValue, ViewModel):
    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return hash(None)

    def __eq__(self, other: Any) -> bool:
        return other is None or isinstance(other, EmptyDomainValueViewModel)

    def __repr__(self) -> str:
        return ""

class DomainValueViewModel(str, DomainValue, ViewModel):
    """
    This class is an ORM to handle a node which is a domain-value datatype. 
    """

    _selected_domain_option: DomainOption = None;
    _lang: str = None;
    _datatype: str = None;

    def __init__(self, domain_id: uuid.UUID, domain_option: DomainOption, lang: str = 'en'):
        """
        Initialize the DomainValueViewModel.

        :param value: The value associated with this view model.
        :param options: A list of options (e.g., for dropdowns or selections).
        :param datatype: The data type of the value (optional).
        """
        self._domain_id = domain_id
        self._domain_option = domain_option
        self._lang = lang

    def __new__(
        cls,
        domain_id: UUID,
        domain_option: DomainOption,
        lang: str = 'en'
    ) -> "DomainValueViewModel":
        text = domain_option.get('text')
        if isinstance(text, dict):
            if lang in text:
                text = text.get(lang)
            elif text:
                text = list(text.values())[0]
            else:
                text = ""
        mystr = super(DomainValueViewModel, cls).__new__(cls, text)
        mystr._domain_id = domain_id
        mystr._domain_option = domain_option
        mystr._lang = lang
        return mystr

    @property
    def enum(self):
        return string_to_enum(self.value)

    @property
    def selected(self) -> bool:
        return self._domain_option.get("selected", False)

    @property
    def domain_id(self) -> uuid.UUID:
        """_summary_
        Method gets the domain node id

        Returns:
            uuid.UUID: This is the domain option id
        """
        return self._domain_id

    @property
    def domain_value_id(self) -> uuid.UUID | None:
        """_summary_
        Method gets the domain option id which has been selected

        Returns:
            uuid.UUID: This is the domain option id
        """
        if (domain_value_id := self._domain_option.get("id")):
            return UUID(domain_value_id)
        return None

    @property
    def text(self) -> DomainOptionText:
        """_summary_
        Method returns the domain option text object
        
        Returns:
            DomainOptionText: The domain option text
        """
        return self._domain_option.get("text")
    
    @property
    def value(self) -> str | None:
        """_summary_
        Method returns the domain option text string based on the lang

        Returns:
            str | None: The domain option text string based on the lang, however if the lang doesn't exisit, then return None
        """

        lang = self._lang or DEFAULT_LANGUAGE

        return self.text.get(lang)


    """ SETTER """
    def lang(self, lang: str) -> str:
        """_summary_
        Method sets the lang and returns the value with the updated lang. Wanted this similar to the string model view

        Args:
            lang (str): This is the language code

        Returns:
            str: This is the updated value with the updated lang
        """

        self._lang  = lang;
        return self.value


class DomainListValueViewModel(UserList[DomainValueViewModel], ViewModel):
    def __init__(
        self,
        domain_value_list_ids: Iterable[str | uuid.UUID],
        make_domain_value: Callable[[uuid.UUID], DomainValueViewModel]
    ):
        UserList.__init__(self)
        self._make_domain_value = make_domain_value
        self._serialize_entries = {}
        for domain_value_id in domain_value_list_ids:
            self.append(domain_value_id)

    def append(self, value):
        if not isinstance(value, DomainValueViewModel):
            value = self._make_domain_value(value)
        super().append(value)

    def remove(self, value):
        if not isinstance(value, DomainValueViewModel):
            value = self._make_domain_value(value)
        super().remove(value)
