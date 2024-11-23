# Quickstart

## For Arches+Django

This guide assumes that you have a running Arches installation in the same
Python environment, with a running database and models.

In this repository, run:

    pip install -e .

If you wish to use the GraphQL auto-API, then you should also run:

    pip install -e .\[graphql\]

To your `settings.py`, add the ORM to the end of your installed apps:

```
    INSTALLED_APPS = (
        ...
        "arches_orm.arches_django.apps.ArchesORMConfig"
    )
```

Furthermore in `settings.py`, you should add the resource models that you wish to
use via the ORM, for example (from Arches for HERs):

    WELL_KNOWN_RESOURCE_MODELS = [{
        "model_name": "Person",
        "graphid": "22477f01-1a44-11e9-b0a9-000d3ab1e588"
    }, {
        "model_name": "Area",
        "graphid": "979aaf0b-7042-11ea-9674-287fcf6a5e72"
    }]

As this could be a big list, you may prefer to create a TOML file to manage the graphs, for example:

    import tomllib
    ...
    with open("wkrm.toml", "r") as wkrm_f:
        WELL_KNOWN_RESOURCE_MODELS = [model for _, model in tomllib.load(wkrm_f).items()]

and then in `wkrm.toml`:

    [Person]
    model_name = "Person"
    graphid = "22477f01-1a44-11e9-b0a9-000d3ab1e588"

    [Area]
    model_name = "Area"
    graphid = "979aaf0b-7042-11ea-9674-287fcf6a5e72"

To use this, first restart Arches and make sure you can log in as normal. Ideally, you
should confirm `python manage.py runserver` successfully runs a local development server
without erroring.

You can experiment with Arches ORM by running:

    python manage.py shell

to launch an interactive Python shell. Then the following commands should work:

    >>> from arches_orm.adapter import admin_everywhere
    >>> admin_everywhere()
    ARCHES ORM ADMINISTRATION MODE ON: use for debugging only, otherwise use the `context_free` or `context` decorator/with statement to achieve this result safely.
    >>> from arches_orm import arches_django
    >>> from arches_orm.models import Person

Firstly, this turns on the admin mode, which means any nodegroup permissions
will be ignored. When writing code in your project, you do not need this call,
but should instead decorate your handler methods and functions with `@context_free`
(or `with context_free():` for small code-blocks) if any resources should load all
nodegroups, or `context(...)` if Arches ORM should filter by a user's permissions.

Secondly, by importing `arches_django`, we tell the ORM that it should get ready
to load from the Arches database, using the `arches.*` Python package. You can
also import `static` to load from JSON and a prototype for `resource_api` backend
exists, which lets you call a remote Arches server behind the scenes instead. You
can make multiple backends available simultaneously, but will have to explicitly
load model classes from a given backend.

Finally, we use the pseudo-module `arches_orm.models` to load resource models.

To create a new Person, you can write:

    >>> p = Person.create()
    >>> n = p.name.append()
    >>> n.full_name = "My Person"
    >>> p.save()
    <AOR:arches-django Person b010e1ac-35a4-45e6-bdf3-a52d9fc27280>

You can then go to `http://localhost:8000/b010e1ac-35a4-45e6-bdf3-a52d9fc27280` in your
browser to see your new Person. Remember to correct the hostname, port (and UUID) for your
local setup.

You can retrieve and modify your Person with, for example:

    >>> p = Person.find("b010e1ac-35a4-45e6-bdf3-a52d9fc27280")
    >>> p.currency.__collection__ <Tab><Tab>
    p.currency.__collection__.Current   p.currency.__collection__.Historic
    p.currency.__collection__.Former    p.currency.__collection__.mro()
    >>> p.currency = p.currency.__collection__.Current
    >>> p.save()
