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

# Define the structure of the 'text' field
class DomainOptionText(TypedDict):
    en: str  # You can add more languages if needed, e.g., "fr": str, "es": str, etc.

# Define the structure of each option
class DomainOption(TypedDict):
    id: UUID
    text: DomainOptionText
    selected: bool

# Define a type alias for a list of options
DomainOptions = List[DomainOption]

# class ValueProtocol(Protocol):
#     """Minimal representation of an Arches concept."""

#     value: str
#     language: str

# class EmptyDomainValueViewModel(CollectionChild, ViewModel):
#     def __bool__(self) -> bool:
#         return False

#     def __hash__(self) -> int:
#         return hash(None)

#     def __eq__(self, other: Any) -> bool:
#         return other is None or isinstance(other, EmptyDomainValueViewModel)

class DomainValueViewModel(ViewModel):
    """
    This class is an ORM to handle a node which is a domain-value datatype. 
    """

    _value_uuid = None;
    _key_by_domain_options = None;
    _selected_domain_option = None;
    _lang = None;
    _domain_options = None;
    _datatype = None;

    def __init__(self, value_uuid: uuid.UUID, domain_options: DomainOptions, datatype: str, lang: str = 'en'):
        """
        Initialize the DomainValueViewModel.

        :param value: The value associated with this view model.
        :param options: A list of options (e.g., for dropdowns or selections).
        :param datatype: The data type of the value (optional).
        """
        self._value_uuid = value_uuid
        self._domain_options = domain_options
        self._datatype = datatype
        self._lang = lang

    """ GETTERS """
    @property
    def key_by_domain_options(self) -> Dict[uuid.UUID, DomainOptions]:
        """_summary_
        This method gets the domain options, however this will return the key as the domain option uuid and the domain option as the value
        
        Returns:
            Dict[uuid.UUID, DomainOptions]: returns the key as the domain option uuid and the domain option as the value
        """
        if self._key_by_domain_options is None:
            self._key_by_domain_options = {option['id']: option for option in self._domain_options}

        return self._key_by_domain_options;

    @property
    def domain_options(self) -> DomainOptions:
        """_summary_
        Method gets the domain options
        
        Returns:
            DomainOptions: Returns the domain options
        """
        return self._domain_options

    @property
    def domain_id(self) -> uuid.UUID:
        """_summary_
        Method gets the domain option id which has been selected

        Returns:
            uuid.UUID: This is the domain option id
        """
        return self._value_uuid

    @property
    def domain(self) -> DomainOption:
        """_summary_
        Method returns the domain option which the domain value is apart of

        Returns:
            DomainOption: This is the domain option which the domain value is apart of
        """
        if (self._selected_domain_option is None):
            self._selected_domain_option = self.key_by_domain_options[self.domain_id]

        return self._selected_domain_option

    @property
    def text(self) -> DomainOptionText:
        """_summary_
        Method returns the domain option text object
        
        Returns:
            DomainOptionText: The domain option text
        """
        return self.domain['text']
    
    @property
    def value(self) -> str | None:
        """_summary_
        Method returns the domain option text string based on the lang

        Returns:
            str | None: The domain option text string based on the lang, however if the lang doesn't exisit, then return None
        """

        if (self.lang not in self.domain['text']):
            return None;

        return self.domain['text'][self.lang]

    @property
    def lang(self) -> str:
        """_summary_
        Method returns the lang returns the current language
        
        Returns:
            str: Returns the current language
        """
        return self._lang
    
    """ SETTERS """
    # @property.setter
    # def lang(self, lang: str):
    #     """_summary_
    #     Method sets the lang, therefore the value changes the lang

    #     Args:
    #         lang (str): This is the language code for example 'en', 'es', 'us'...
    #     """

    #     self._lang = lang;


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
