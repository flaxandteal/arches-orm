# Module arches_orm.view_models.concepts

??? example "View Source"
        from typing import Union, Callable, Protocol

        import uuid

        from functools import lru_cache

        from collections import UserList

        from collections.abc import Iterable

        from ._base import (

            ViewModel,

        )

        class ConceptProtocol(Protocol):

            """Minimal representation of an Arches concept."""

            value: str

            language: str

        

        class ConceptValueViewModel(str, ViewModel):

            """Wraps a concept, allowing interrogation.

            Subclasses str, so it can be handled like a string enum, but keeps

            the `.value`, `.lang` and `.text` properties cached, so you can

            find out more.

            """

            _concept_value_id: uuid.UUID

            _concept_value_cb: Callable[[uuid.UUID], ConceptProtocol]

            def __eq__(self, other):

                return self.conceptid == other.conceptid

            def __new__(

                cls,

                concept_value_id: Union[str, uuid.UUID],

                concept_value_cb,

            ):

                _concept_value_id: uuid.UUID = (

                    concept_value_id

                    if isinstance(concept_value_id, uuid.UUID)

                    else uuid.UUID(concept_value_id)

                )

                mystr = super(ConceptValueViewModel, cls).__new__(cls, str(_concept_value_id))

                mystr._concept_value_id = _concept_value_id

                mystr._concept_value_cb = concept_value_cb

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

                return self._concept_value_cb(self._concept_value_id)

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

        

        class ConceptListValueViewModel(UserList, ViewModel):

            """Wraps a concept list, allowing interrogation.

            Subclasses list, so its members can be handled like a string enum, but keeps

            the `.value`, `.lang` and `.text` properties cached, so you can

            find out more.

            """

            def __init__(

                self,

                concept_value_ids: Iterable[str | uuid.UUID],

                make_cb,

            ):

                for concept_value_id in concept_value_ids:

                    self.append(concept_value_id)

                self._make_cb = make_cb

            def append(self, value):

                if not isinstance(value, ConceptValueViewModel):

                    value = self._make_cb(value)

                super().append(value)

            def remove(self, value):

                if not isinstance(value, ConceptValueViewModel):

                    value = self._make_cb(value)

                super().remove(value)

## Classes

### ConceptListValueViewModel

```python3
class ConceptListValueViewModel(
    concept_value_ids: collections.abc.Iterable[str | uuid.UUID],
    make_cb
)
```

Wraps a concept list, allowing interrogation.

Subclasses list, so its members can be handled like a string enum, but keeps
the `.value`, `.lang` and `.text` properties cached, so you can
find out more.

??? example "View Source"
        class ConceptListValueViewModel(UserList, ViewModel):

            """Wraps a concept list, allowing interrogation.

            Subclasses list, so its members can be handled like a string enum, but keeps

            the `.value`, `.lang` and `.text` properties cached, so you can

            find out more.

            """

            def __init__(

                self,

                concept_value_ids: Iterable[str | uuid.UUID],

                make_cb,

            ):

                for concept_value_id in concept_value_ids:

                    self.append(concept_value_id)

                self._make_cb = make_cb

            def append(self, value):

                if not isinstance(value, ConceptValueViewModel):

                    value = self._make_cb(value)

                super().append(value)

            def remove(self, value):

                if not isinstance(value, ConceptValueViewModel):

                    value = self._make_cb(value)

                super().remove(value)

------

#### Ancestors (in MRO)

* collections.UserList
* collections.abc.MutableSequence
* collections.abc.Sequence
* collections.abc.Reversible
* collections.abc.Collection
* collections.abc.Sized
* collections.abc.Iterable
* collections.abc.Container
* arches_orm.view_models._base.ViewModel

#### Methods

    
#### append

```python3
def append(
    self,
    value
)
```

S.append(value) -- append value to the end of the sequence

??? example "View Source"
            def append(self, value):

                if not isinstance(value, ConceptValueViewModel):

                    value = self._make_cb(value)

                super().append(value)

    
#### clear

```python3
def clear(
    self
)
```

S.clear() -> None -- remove all items from S

??? example "View Source"
            def clear(self):

                self.data.clear()

    
#### copy

```python3
def copy(
    self
)
```

??? example "View Source"
            def copy(self):

                return self.__class__(self)

    
#### count

```python3
def count(
    self,
    item
)
```

S.count(value) -> integer -- return number of occurrences of value

??? example "View Source"
            def count(self, item):

                return self.data.count(item)

    
#### extend

```python3
def extend(
    self,
    other
)
```

S.extend(iterable) -- extend sequence by appending elements from the iterable

??? example "View Source"
            def extend(self, other):

                if isinstance(other, UserList):

                    self.data.extend(other.data)

                else:

                    self.data.extend(other)

    
#### index

```python3
def index(
    self,
    item,
    *args
)
```

S.index(value, [start, [stop]]) -> integer -- return first index of value.

Raises ValueError if the value is not present.

Supporting start and stop arguments is optional, but
recommended.

??? example "View Source"
            def index(self, item, *args):

                return self.data.index(item, *args)

    
#### insert

```python3
def insert(
    self,
    i,
    item
)
```

S.insert(index, value) -- insert value before index

??? example "View Source"
            def insert(self, i, item):

                self.data.insert(i, item)

    
#### pop

```python3
def pop(
    self,
    i=-1
)
```

S.pop([index]) -> item -- remove and return item at index (default last).

Raise IndexError if list is empty or index is out of range.

??? example "View Source"
            def pop(self, i=-1):

                return self.data.pop(i)

    
#### remove

```python3
def remove(
    self,
    value
)
```

S.remove(value) -- remove first occurrence of value.

Raise ValueError if the value is not present.

??? example "View Source"
            def remove(self, value):

                if not isinstance(value, ConceptValueViewModel):

                    value = self._make_cb(value)

                super().remove(value)

    
#### reverse

```python3
def reverse(
    self
)
```

S.reverse() -- reverse *IN PLACE*

??? example "View Source"
            def reverse(self):

                self.data.reverse()

    
#### sort

```python3
def sort(
    self,
    /,
    *args,
    **kwds
)
```

??? example "View Source"
            def sort(self, /, *args, **kwds):

                self.data.sort(*args, **kwds)

### ConceptProtocol

```python3
class ConceptProtocol(
    *args,
    **kwargs
)
```

Minimal representation of an Arches concept.

??? example "View Source"
        class ConceptProtocol(Protocol):

            """Minimal representation of an Arches concept."""

            value: str

            language: str

------

#### Ancestors (in MRO)

* typing.Protocol
* typing.Generic

### ConceptValueViewModel

```python3
class ConceptValueViewModel(
    /,
    *args,
    **kwargs
)
```

Wraps a concept, allowing interrogation.

Subclasses str, so it can be handled like a string enum, but keeps
the `.value`, `.lang` and `.text` properties cached, so you can
find out more.

??? example "View Source"
        class ConceptValueViewModel(str, ViewModel):

            """Wraps a concept, allowing interrogation.

            Subclasses str, so it can be handled like a string enum, but keeps

            the `.value`, `.lang` and `.text` properties cached, so you can

            find out more.

            """

            _concept_value_id: uuid.UUID

            _concept_value_cb: Callable[[uuid.UUID], ConceptProtocol]

            def __eq__(self, other):

                return self.conceptid == other.conceptid

            def __new__(

                cls,

                concept_value_id: Union[str, uuid.UUID],

                concept_value_cb,

            ):

                _concept_value_id: uuid.UUID = (

                    concept_value_id

                    if isinstance(concept_value_id, uuid.UUID)

                    else uuid.UUID(concept_value_id)

                )

                mystr = super(ConceptValueViewModel, cls).__new__(cls, str(_concept_value_id))

                mystr._concept_value_id = _concept_value_id

                mystr._concept_value_cb = concept_value_cb

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

                return self._concept_value_cb(self._concept_value_id)

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

------

#### Ancestors (in MRO)

* builtins.str
* arches_orm.view_models._base.ViewModel

#### Static methods

    
#### maketrans

```python3
def maketrans(
    ...
)
```

Return a translation table usable for str.translate().

If there is only one argument, it must be a dictionary mapping Unicode
ordinals (integers) or characters to Unicode ordinals, strings or None.
Character keys will be then converted to ordinals.
If there are two arguments, they must be strings of equal length, and
in the resulting dictionary, each character in x will be mapped to the
character at the same position in y. If there is a third argument, it
must be a string, whose characters will be mapped to None in the result.

#### Instance variables

```python3
concept
```

```python3
conceptid
```

```python3
lang
```

```python3
text
```

```python3
value
```

#### Methods

    
#### capitalize

```python3
def capitalize(
    self,
    /
)
```

Return a capitalized version of the string.

More specifically, make the first character have upper case and the rest lower
case.

    
#### casefold

```python3
def casefold(
    self,
    /
)
```

Return a version of the string suitable for caseless comparisons.

    
#### center

```python3
def center(
    self,
    width,
    fillchar=' ',
    /
)
```

Return a centered string of length width.

Padding is done using the specified fill character (default is a space).

    
#### count

```python3
def count(
    ...
)
```

S.count(sub[, start[, end]]) -> int

Return the number of non-overlapping occurrences of substring sub in
string S[start:end].  Optional arguments start and end are
interpreted as in slice notation.

    
#### encode

```python3
def encode(
    self,
    /,
    encoding='utf-8',
    errors='strict'
)
```

Encode the string using the codec registered for encoding.

encoding
  The encoding in which to encode the string.
errors
  The error handling scheme to use for encoding errors.
  The default is 'strict' meaning that encoding errors raise a
  UnicodeEncodeError.  Other possible values are 'ignore', 'replace' and
  'xmlcharrefreplace' as well as any other name registered with
  codecs.register_error that can handle UnicodeEncodeErrors.

    
#### endswith

```python3
def endswith(
    ...
)
```

S.endswith(suffix[, start[, end]]) -> bool

Return True if S ends with the specified suffix, False otherwise.
With optional start, test S beginning at that position.
With optional end, stop comparing S at that position.
suffix can also be a tuple of strings to try.

    
#### expandtabs

```python3
def expandtabs(
    self,
    /,
    tabsize=8
)
```

Return a copy where all tab characters are expanded using spaces.

If tabsize is not given, a tab size of 8 characters is assumed.

    
#### find

```python3
def find(
    ...
)
```

S.find(sub[, start[, end]]) -> int

Return the lowest index in S where substring sub is found,
such that sub is contained within S[start:end].  Optional
arguments start and end are interpreted as in slice notation.

Return -1 on failure.

    
#### format

```python3
def format(
    ...
)
```

S.format(*args, **kwargs) -> str

Return a formatted version of S, using substitutions from args and kwargs.
The substitutions are identified by braces ('{' and '}').

    
#### format_map

```python3
def format_map(
    ...
)
```

S.format_map(mapping) -> str

Return a formatted version of S, using substitutions from mapping.
The substitutions are identified by braces ('{' and '}').

    
#### index

```python3
def index(
    ...
)
```

S.index(sub[, start[, end]]) -> int

Return the lowest index in S where substring sub is found,
such that sub is contained within S[start:end].  Optional
arguments start and end are interpreted as in slice notation.

Raises ValueError when the substring is not found.

    
#### isalnum

```python3
def isalnum(
    self,
    /
)
```

Return True if the string is an alpha-numeric string, False otherwise.

A string is alpha-numeric if all characters in the string are alpha-numeric and
there is at least one character in the string.

    
#### isalpha

```python3
def isalpha(
    self,
    /
)
```

Return True if the string is an alphabetic string, False otherwise.

A string is alphabetic if all characters in the string are alphabetic and there
is at least one character in the string.

    
#### isascii

```python3
def isascii(
    self,
    /
)
```

Return True if all characters in the string are ASCII, False otherwise.

ASCII characters have code points in the range U+0000-U+007F.
Empty string is ASCII too.

    
#### isdecimal

```python3
def isdecimal(
    self,
    /
)
```

Return True if the string is a decimal string, False otherwise.

A string is a decimal string if all characters in the string are decimal and
there is at least one character in the string.

    
#### isdigit

```python3
def isdigit(
    self,
    /
)
```

Return True if the string is a digit string, False otherwise.

A string is a digit string if all characters in the string are digits and there
is at least one character in the string.

    
#### isidentifier

```python3
def isidentifier(
    self,
    /
)
```

Return True if the string is a valid Python identifier, False otherwise.

Call keyword.iskeyword(s) to test whether string s is a reserved identifier,
such as "def" or "class".

    
#### islower

```python3
def islower(
    self,
    /
)
```

Return True if the string is a lowercase string, False otherwise.

A string is lowercase if all cased characters in the string are lowercase and
there is at least one cased character in the string.

    
#### isnumeric

```python3
def isnumeric(
    self,
    /
)
```

Return True if the string is a numeric string, False otherwise.

A string is numeric if all characters in the string are numeric and there is at
least one character in the string.

    
#### isprintable

```python3
def isprintable(
    self,
    /
)
```

Return True if the string is printable, False otherwise.

A string is printable if all of its characters are considered printable in
repr() or if it is empty.

    
#### isspace

```python3
def isspace(
    self,
    /
)
```

Return True if the string is a whitespace string, False otherwise.

A string is whitespace if all characters in the string are whitespace and there
is at least one character in the string.

    
#### istitle

```python3
def istitle(
    self,
    /
)
```

Return True if the string is a title-cased string, False otherwise.

In a title-cased string, upper- and title-case characters may only
follow uncased characters and lowercase characters only cased ones.

    
#### isupper

```python3
def isupper(
    self,
    /
)
```

Return True if the string is an uppercase string, False otherwise.

A string is uppercase if all cased characters in the string are uppercase and
there is at least one cased character in the string.

    
#### join

```python3
def join(
    self,
    iterable,
    /
)
```

Concatenate any number of strings.

The string whose method is called is inserted in between each given string.
The result is returned as a new string.

Example: '.'.join(['ab', 'pq', 'rs']) -> 'ab.pq.rs'

    
#### ljust

```python3
def ljust(
    self,
    width,
    fillchar=' ',
    /
)
```

Return a left-justified string of length width.

Padding is done using the specified fill character (default is a space).

    
#### lower

```python3
def lower(
    self,
    /
)
```

Return a copy of the string converted to lowercase.

    
#### lstrip

```python3
def lstrip(
    self,
    chars=None,
    /
)
```

Return a copy of the string with leading whitespace removed.

If chars is given and not None, remove characters in chars instead.

    
#### partition

```python3
def partition(
    self,
    sep,
    /
)
```

Partition the string into three parts using the given separator.

This will search for the separator in the string.  If the separator is found,
returns a 3-tuple containing the part before the separator, the separator
itself, and the part after it.

If the separator is not found, returns a 3-tuple containing the original string
and two empty strings.

    
#### removeprefix

```python3
def removeprefix(
    self,
    prefix,
    /
)
```

Return a str with the given prefix string removed if present.

If the string starts with the prefix string, return string[len(prefix):].
Otherwise, return a copy of the original string.

    
#### removesuffix

```python3
def removesuffix(
    self,
    suffix,
    /
)
```

Return a str with the given suffix string removed if present.

If the string ends with the suffix string and that suffix is not empty,
return string[:-len(suffix)]. Otherwise, return a copy of the original
string.

    
#### replace

```python3
def replace(
    self,
    old,
    new,
    count=-1,
    /
)
```

Return a copy with all occurrences of substring old replaced by new.

count
    Maximum number of occurrences to replace.
    -1 (the default value) means replace all occurrences.

If the optional argument count is given, only the first count occurrences are
replaced.

    
#### rfind

```python3
def rfind(
    ...
)
```

S.rfind(sub[, start[, end]]) -> int

Return the highest index in S where substring sub is found,
such that sub is contained within S[start:end].  Optional
arguments start and end are interpreted as in slice notation.

Return -1 on failure.

    
#### rindex

```python3
def rindex(
    ...
)
```

S.rindex(sub[, start[, end]]) -> int

Return the highest index in S where substring sub is found,
such that sub is contained within S[start:end].  Optional
arguments start and end are interpreted as in slice notation.

Raises ValueError when the substring is not found.

    
#### rjust

```python3
def rjust(
    self,
    width,
    fillchar=' ',
    /
)
```

Return a right-justified string of length width.

Padding is done using the specified fill character (default is a space).

    
#### rpartition

```python3
def rpartition(
    self,
    sep,
    /
)
```

Partition the string into three parts using the given separator.

This will search for the separator in the string, starting at the end. If
the separator is found, returns a 3-tuple containing the part before the
separator, the separator itself, and the part after it.

If the separator is not found, returns a 3-tuple containing two empty strings
and the original string.

    
#### rsplit

```python3
def rsplit(
    self,
    /,
    sep=None,
    maxsplit=-1
)
```

Return a list of the substrings in the string, using sep as the separator string.

sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \\n \\r \\t \\f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits (starting from the left).
    -1 (the default value) means no limit.

Splitting starts at the end of the string and works to the front.

    
#### rstrip

```python3
def rstrip(
    self,
    chars=None,
    /
)
```

Return a copy of the string with trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

    
#### split

```python3
def split(
    self,
    /,
    sep=None,
    maxsplit=-1
)
```

Return a list of the substrings in the string, using sep as the separator string.

sep
    The separator used to split the string.

    When set to None (the default value), will split on any whitespace
    character (including \\n \\r \\t \\f and spaces) and will discard
    empty strings from the result.
  maxsplit
    Maximum number of splits (starting from the left).
    -1 (the default value) means no limit.

Note, str.split() is mainly useful for data that has been intentionally
delimited.  With natural text that includes punctuation, consider using
the regular expression module.

    
#### splitlines

```python3
def splitlines(
    self,
    /,
    keepends=False
)
```

Return a list of the lines in the string, breaking at line boundaries.

Line breaks are not included in the resulting list unless keepends is given and
true.

    
#### startswith

```python3
def startswith(
    ...
)
```

S.startswith(prefix[, start[, end]]) -> bool

Return True if S starts with the specified prefix, False otherwise.
With optional start, test S beginning at that position.
With optional end, stop comparing S at that position.
prefix can also be a tuple of strings to try.

    
#### strip

```python3
def strip(
    self,
    chars=None,
    /
)
```

Return a copy of the string with leading and trailing whitespace removed.

If chars is given and not None, remove characters in chars instead.

    
#### swapcase

```python3
def swapcase(
    self,
    /
)
```

Convert uppercase characters to lowercase and lowercase characters to uppercase.

    
#### title

```python3
def title(
    self,
    /
)
```

Return a version of the string where each word is titlecased.

More specifically, words start with uppercased characters and all remaining
cased characters have lower case.

    
#### translate

```python3
def translate(
    self,
    table,
    /
)
```

Replace each character in the string using the given translation table.

table
    Translation table, which must be a mapping of Unicode ordinals to
    Unicode ordinals, strings, or None.

The table must implement lookup/indexing via __getitem__, for instance a
dictionary or list.  If this operation raises LookupError, the character is
left untouched.  Characters mapped to None are deleted.

    
#### upper

```python3
def upper(
    self,
    /
)
```

Return a copy of the string converted to uppercase.

    
#### zfill

```python3
def zfill(
    self,
    width,
    /
)
```

Pad a numeric string with zeros on the left, to fill a field of the given width.

The string is never truncated.