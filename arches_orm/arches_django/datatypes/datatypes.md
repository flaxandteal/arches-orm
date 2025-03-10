# Introduction
Welcome to the datatypes section. This section is mainily used towards hooking up a tile value datatype to a datatype class and then hooking that datatype class up towards a view model (arches_orm/view_models/*.py). The purpose of these data models is to setup the data towards the view model, register the method withinn the class for the tile datatype and return the value towards the tile data.

## as_tile_data
This retreives only the value from the tile, therefore if the user types `Person.name.full_name`, it returns the tile value instead of the view model classs, however we can still use the view model methods on top for example since this type is a string, we can use the method `lang()` within `arches_orm/view_models/string.py` and active the method like this `Person.name.full_name.lang()`.

This is defined by using `as_tile_data` on certain properties with the view_model class passed in as a parameter. 
```python
@string.as_tile_data
def s_as_tile_data(string):
    return string._value
```

## REGISTER
The section talks about the pointer method towards a datatype and how the method is registered. Now its important how the register classes calls these methods, therefore I've made a step by step below:
1. The tile data is gained, looped and for each tile data it calls _make_pseudo_node_cls within `wrapper.py`
2. _make_pseudo_node_cls it calls classes `PseudoNodeList`, `PseudoNodeUnavailable` or `PseudoNodeValue` within `pseudo_node/pseudo_nodes.py`
3. The classes `PseudoNodeList`, `PseudoNodeUnavailable` & `PseudoNodeValue` all have a `__init__` method which takes in the parameter `get_view_model_for_datatype` which is the method `get_view_model_for_datatype` in `datatypes/_register.py`.
4. This method calls `make` in `ViewModelRegister` and finally within this make method looks for the datatype classes 

Below is our the method is registered towards that datatype class towards a string, all you have to do is define `@REGISTER("DATATYPE")` above the method. Please keep in mind that this datatype class has to be exactly the same keyword within the table `nodes` and in the column `datatype` or this register method will not work properly.
```python
@REGISTER("string")
def string(tile, node, value: dict | None, _, __, ___, string_datatype):
```