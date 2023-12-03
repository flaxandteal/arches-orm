# (Unofficial) Arches ORM [EXPERIMENTAL]

This provides simple (server-side) access to Arches resources from Python
as Python objects. It makes no guarantees about efficiency or type-accuracy
but such issues raised will be addressed as far as possible.

## Well-known Resource Models

To provide a partial boundary, this package expects a settings object called
`WELL_KNOWN_RESOURCE_MODELS` to list, at least, the models that should be
wrapped by this system.

It should be a list:

    WELL_KNOWN_RESOURCE_MODELS = [
        {
            "model_name": "Person",
            "graphid": "4110f743-1a44-11e9-9a37-000d3ab1e500",
            "nodes": {}, # optional additional configuration
            "to_string": lambda wkrm: str(wkrm) # optional callback for stringifying
        }
    ]

You must _not_ take this list as an exclusive boundary of data that can be accessed.

## Hooks

This package also contains experimental functionality for hooking tile saves,
so that client code can use the `MyModel.post_save` signal to get well-known
resource model events. To avoid any unintended overhead, it does not load
unless explicitly turned on with `arches_orm.add_hooks()`.

## Tests

Note that the tests require `spatialite` and so a Python that allows Sqlite3
extension loading:

    PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions" pyenv install 3.10.10

## Thanks

Particular thanks to the funders of this work, and to the Arches community for
their work on which this builds. Particular thanks to Historic England's team
for the underlying resource models used in the test-cases.
