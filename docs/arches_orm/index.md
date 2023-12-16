# Module arches_orm

??? example "View Source"
        ## Note that some of this is based heavily on

        ## github.com/archesproject/arches

        ## and should be considered AGPLv3.

        import logging

        logger = logging.getLogger(__name__)

        

        def add_hooks() -> set[str]:

            from .hooks import HOOKS

            return HOOKS

## Sub-modules

* [arches_orm.arches_django](arches_django/)
* [arches_orm.hooks](hooks/)
* [arches_orm.models](models/)
* [arches_orm.utils](utils/)
* [arches_orm.view_models](view_models/)
* [arches_orm.wkrm](wkrm/)
* [arches_orm.wrapper](wrapper/)

## Variables

```python3
logger
```

## Functions

    
### add_hooks

```python3
def add_hooks(
    
) -> set[str]
```

??? example "View Source"
        def add_hooks() -> set[str]:

            from .hooks import HOOKS

            return HOOKS