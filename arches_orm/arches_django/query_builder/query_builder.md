# Welcome to the Query Builder system
The query builder purpose is to get WKRI with contained tile data which is wrapped around view_model classes. The query builder allows you to preform some queries on these WKRI with node alias, instead of using the entire node id as the node id is UUID and the node alias is a custom key. Since the fastest way to pull data from the database is to use the database tools, the query builder takes advantage of the builder pattern https://refactoring.guru/design-patterns/builder to build Django quries which intern build SQL quries.

The query builder quries are split up into 3 different sections:
- **Filters**: This is used filtering the data on the Django quries, therefore quries such as where(), or_where() would be considered filtering
- **Modifiers**: This is used towards modifying the records (So not removing but adjusting), therefore quries such as order_by(), lazy()
- **Selectors**: This is used towards selecting the records (So obtaining the data in a certain way), therefore quries such as get(), all(), first(), offset()

## How Does the Query Builder System Work
The query builder takes advantage of the builder pattern https://refactoring.guru/design-patterns/builder to build Django quries which intern build SQL quries. The main area of data is the [Query Builder](./query_builder.py) which holds variables that are used for filtering, excluding, annotations, order by, etc. towards our SQL query.

We set the [Query Builder](./query_builder.py) by using the [Filters](./children_classes/filters.py), [Modifiers](./children_classes/modifiers.py) & [Selectors](./children_classes/selectors.py) which is describe futher below.

### Annotations and Expressions
When filtering in Django, we can use a query like `person.filter(age__gt=40)` to retrieve all person records where the age is greater than 40. However, in our case, the value is stored inside a JSONB column—tiledata in the database (referred to as data in the model). This introduces challenges when querying, which I’ve addressed using expressions and annotations, as explained below:

#### Accessing a value within a JSON_B column
The `tiledata` field is a JSONB column, so a query like `person.filter(age__gt=40)` won't work. Instead, you need to use the full path to the nested key, such as p`erson.filter(male__aidan__age__gt=40)`. Django uses double underscores (__) to navigate through keys in the JSONB structure.

#### UUID as keys within the JSON_B column
When the user tries to run `person.filter(firstname__en__value="Bob")`, it won't work because the tiledata uses UUIDs as keys. For example, the JSON structure of tiledata shows that instead of `firstname`, the key is actually the `node id`.
```json
{
  "127095f5-c05e-11e9-bb57-a4d18cec433a": {
    "de": {
      "value": "",
      "direction": "ltr"
    },
    "el": {
      "value": "",
      "direction": "ltr"
    },
    "en": {
      "value": "Aidan",
      "direction": "ltr"
    },
    "fr": {
      "value": "",
      "direction": "ltr"
    },
    "pt": {
      "value": "",
      "direction": "ltr"
    },
    "ru": {
      "value": "",
      "direction": "ltr"
    },
    "zh": {
      "value": "",
      "direction": "ltr"
    },
    "en-US": {
      "value": "",
      "direction": "ltr"
    },
    "en-us": {
      "value": "",
      "direction": "ltr"
    }
  },
  "6b7fc7e2-0279-11ed-b140-0242ac180008": null,
  "e8fe4f4e-027a-11ed-9dee-0242ac180008": null
}
```
This problem was solved using [annotations](./annotations/annotations.py) (*In Django, annotations are used to add calculated fields like counts, sums, or custom expressions to each object in a queryset using database-level aggregation*). In our case, we use annotations to extract a value and attach the node alias instead of using the node id. We also perform expression-based cases, which are explained more in [Datatypes Extractions](#datatypes-extractions).

For example, an annotation would look like this:
```python
person.annotate(
    'firstname'=F('tiledata__127095f5-c05e-11e9-bb57-a4d18cec433a__en__value')
)
```
With the example above, our queryset would include something like `{"firstname": "Aidan"}`, so we can now filter directly using firstname like this:
```python
person.annotate(
    'firstname'=F('tiledata__127095f5-c05e-11e9-bb57-a4d18cec433a__en__value')
).filter(firstname="Aidan")
```

#### Datatypes Extractions
The main issue within this section is the handling of extracting the value for example we use the [F](https://www.youtube.com/watch?v=NDOYWw0tDgw&t=289s&ab_channel=BugBytes) expression to simply extract the value from the JSON_B coumn (tiledata)
```python
person.annotate(
    'firstname'=F('tiledata__127095f5-c05e-11e9-bb57-a4d18cec433a__en__value')
).filter(firstname="Aidan")
```

The issue is with certain datatypes comes with complex values for example domain values have a value of a UUID which relates to a key value within node options, concept value again has a UUID which relates to a concept key within a concept list, etc. In this instance we will discuss more in depth about expressions and an example of solving the domain value issue datatype expression.

```python
def postgresql_expression_domain_value(node: Node, additional_keys: List[str] = None) -> ExpressionDomainValueReturnType:
    key_lang = additional_keys[0] if additional_keys and len(additional_keys) >= 1 else 'en'
    options = node.config.get('options', [])
    dynamic_annotation_key = domain_value_annotation_key(node.alias)

    when_conditions = []
    for option in options:
        node_id = option.get("id")
        selected_option = option['text'][key_lang]

        when_conditions.append(
            When(**{dynamic_annotation_key: node_id}, then=Value(selected_option))
        )

    case_expression = Case(*when_conditions, default=Value(None))

    # ! Unfortually, When() as some issues with running database functions as conditions, therefore we use default to extract the domain value id
    # ! and then use this default key as the condition to check which node option it is paired with
    return {
        "default": F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{node.nodeid}'),
        "annotation": ExpressionWrapper(
            case_expression,
            output_field=CharField()
        )
    }
```

The above demonstrates the solution for extracting the correct domain value and attaching it to an annotation. First, we extract the UUID and assign it to a key named `"default"` using:
`"default": F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{node.nodeid}')`.
This provides the base key linked to the relevant UUID. Next, we define another annotation that references this default annotation UUID and uses [WHEN](https://www.youtube.com/watch?v=beVGYjMSRRk&t=1130s&ab_channel=BugBytes) clauses to iterate through the node options. When a WHEN condition is met, the corresponding node option value is selected.

We define a default annotation separately because extracting the related UUID within a single annotation proved challenging. By splitting the logic into two annotations, we were able to achieve the desired outcome more reliably. This is the main reason for the [Query Builder](./query_builder.py) to have `_before_annotations`

```python
person.annotate(
    "default": F(f'{RESOURCE_MERGED_TILE_DATA_KEY}__{node.nodeid}'),
).annotate(
    "annotation": ExpressionWrapper(
        case_expression,
        output_field=CharField()
    )
)
```

#### Database Compatibility
When developing the [Datatypes Extractions](#datatypes-extractions) for local tests on arches orm (SQLite) and coral (PostgreSQL), I noticed that I ran into some compatibility issues as some of the datatypes extractions did not work properly or at all. I figured out that the main cause of issue was that PostgreSQL & SQLite had different syntax or they didn't have the same internal methods.

**SQLite**
```python
class JsonGroupArray(Aggregate):
    function = 'JSON_GROUP_ARRAY'
    output_field = JSONField()
    template = '%(function)s(%(distinct)s%(expressions)s)'

class JsonExtract(Func):
    function = 'json_extract'
    output_field = JSONField()
    template = "json_extract(%(expressions)s, '$[0]')"
```

**PostgreSQL**
```python
class JsonBAgg(Aggregate):
    function = 'jsonb_agg'
    output_field = JSONField()
    template = '%(function)s(%(distinct)s%(expressions)s)'
```

As you can see above, for extracting and merging JSON_B columns in the database, that both of these database services use compelety different methods as SQLite doesn't have `jsonb_agg`, therefore addional functions is required for SQLite instead of PostgreSQL.

This issue was fixed by pointing to different expression methods depending on the current `database_engine` in the Django system. [Expressions](./annotations/expressions/expressions.py) will either use methods from [SQLite](./annotations/expressions/expressions_sqlite.py) or [PostgreSQL](./annotations/expressions/expressions_postgresql.py).


#### Tiledata have sperate records but the same resource instance ids

| tileid                                 | tiledata                                                                                                                                                                   | nodegroupid                              | parenttileid | resourceinstanceid                     | sortorder | provisionaledits |
|----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|---------------|----------------------------------------|-----------|------------------|
| 01a08744-992e-4950-a6da-d71e26cd4a35   | {"c0bde702-69c9-11ef-903c-0242ac120005": {"en": {"value": "Licensing", "direction": "ltr"}}}                                                                               | c0bde702-69c9-11ef-903c-0242ac120005      | NULL          | c189d783-013b-a685-3f07-f9aa8aef85ab   | 0         | NULL             |
| d068ff95-22d0-47d5-af43-a6c74563f65a   | {"d124c1a6-6780-11ef-9f42-0242ac120006": {"en": {"value": "licensing-workflow", "direction": "ltr"}}}                                                                     | d124c1a6-6780-11ef-9f42-0242ac120006      | NULL          | c189d783-013b-a685-3f07-f9aa8aef85ab   | 0         | NULL             |

Above is an example of the issue: you can see that there are two rows in the table with the same **resourceinstanceid**. This causes problems for certain queries. For example, if you run:
```python
person.where(license="Licensing", licensing_workflow="licensing-workflow").get()
```
This will return nothing—even though the condition is true and should return at least one record. The issue is that the relevant `tiledata` values for the filter are split across separate rows. Django evaluates filter conditions row-by-row, so it doesn't find a single row that satisfies both conditions.

To solve this, I merged or grouped the `tiledata` entries based on the resourceinstanceid, then queried the merged result instead.

Inside [expressions](./annotations/expressions/expressions.py), there's a method called `expresion_merge_tile_json_data`. This method merges the JSONB `tiledata` fields and stores the result in an annotation called RESOURCE_MERGED_TILE_DATA_KEY, which is defined in [config](./config.py).

This merged key is then used across both [expression_postgresql](./annotations/expressions/expressions_postgresql.py) and [expresion_sqlite](./annotations/expressions/expressions_sqlite.py) to ensure consistent querying on the combined JSON.

Finally, in [selectors](./children_classes/selectors.py), RESOURCE_MERGED_TILE_DATA_KEY is added to the queryset so that it's always available for querying.
```python
queryset_tiles = queryset_tiles.annotate(
    **{RESOURCE_MERGED_TILE_DATA_KEY: annotation_resource_merge_tile_data(self._instance_query_builder._database_engine)}
).distinct().annotate(
    **self._instance_query_builder._before_annotations
).annotate(
    **annotations
)
```

### Insight on Progress
In this section will describe an example of the process for filtering, modifiying and selecting data. We will assume the query 
```python
Person.where(firsname__de__contains='Aid').order_by('firstname').get()
```

#### Filter - where(firsname__contains='Aid')
![Alt text](./Filter%20Structurer.png)

##### 1st - Accessing where
The user access the init method `where` on the wrapper which points to a exposed method on the query builder that is gained from filters

##### 2nd - The loop
The conditions are looped so in this case, it's just a single loop with the key `firsname__contains` and value `'Aid'`. 

Within these loop we format the key to know the field key `firstname`, the addional keys [`de`] and the sepertor `contains`.

Next we define the conditions inside locally `_filters` & `_excludes` for future usage.

```python
    if field_lookup == 'equal':
        self._filters[field_key] = value
    elif field_lookup in NOT_EQUAL_KEYS:
        self._excludes[field_key] = value
    else:
        self._filters[field_key + "__" + field_lookup] = value
```

Finally within the loop we call `set_annotation()` from the query builder

The `set_annotation()` method instead the [Query Builder](./query_builder.py) will setup the annotation towards the key and pick the apporatie expression for value extraction from the JSON_B column. Read [here](#annotations-and-expressions) to learn more.

The `_annotations` & `_before_annotations` is set within [Query Builder](./query_builder.py) using the method `set_annotation`

##### 3rd - Setting up _filter_structures and _exclude_structures
Once the loop is completed the `_filter_structures` & `_exclude_structures` is set using the local `_filters` & `_excludes`. The `_filter_structures` & `_exclude_structures` are variables defined within [Query Builder](./query_builder.py)


##### 4th - What's returned
The same instance of the [Query Builder](./query_builder.py) is returned, therefore offering chainable through `__getattr__`

#### Modifiter


## The file structure
In this section describes some of the files structures to help fully understand the purpose of each file and where future development code be defined within

### query_builder.py
This file is the index file of the entire query builder system, its class contained within the file is used to utilize the query builder system. This file contains calling the queries to obtain the tiles, converting the tiles values towards to view model, creating wkri instances, setting up annotations, the data which is used towards filtering, modifying and selecting towards the queries, etc.

Please don't get confused the **filtering, modifying and selecting data structures are defined** within the query_builder.py class, however **defining the data towards these structures are ran through the children_classes**. The methods are exposed from the children classes for example `children_classes/filters.py` methods are accessed by `query_builder.py` with the utilizing of the `__getattr__` method. This is also the main reason these classes are called children classes.

### children_classes/filters.py
This child class defines the filter query methods so things such as `where()`, `or_where()`. These methods act like setters which set data towards variables filter_structures, exclude_structurers & annotations defined within the `query_builder.py`

### children_classes/modifiers.py
This child class defines the modifiers query methods so things such as `lazy()`, `order_by()`. These methods act like setters which set data towards variables _lazy_mode, exclude_structurers, order_by & annotations defined within the `query_builder.py`

### children_classes/selectors.py
This child class defines the selectors query methods for example `all()`, `get()`, `first()`, etc. These methods set up a callback method towards the method "*create_wkri_with_datatype_values*" on the `query_builder.py`. These methods define filtering, excluding, order by, offset data, annotations towards the Django system within the callback method. 

### expressions.py
This file is used towards defining expressions towards annotations towards JSON columns storaged within the database for example `age_annotation=data__ec03c1fd-e250-46be-b27a-d28d4d32762c`. In this file, defines datatypes towards tile data as each datatype is stored differently within the JSON column and it also might need some casting aswel, for example field_output=NumberField(). Overall, these expressions help with annotations setup, therefore filtering becomes exetremly simpler as we can use the node alias, instead of the node uuid and this also extracts the value to query agasint from the JSON column.

### config.py
This file stores variables which are globally used within the query_builder. Current the variables stored are the custom keys which the user can use to query certain operations for example `INSENSITIVE_CONTAINS_KEYS = ['ict', 'icontains']` -> `person.where(name__ict='test').get()` or `person.where(name__icontains='test').get()` but both ways preform a insenitive contains key operation

### utilities.py
This file is used to store common methods which can be accross the query builder system for example, the method "transform_filter_exclude_structure_towards_query", transforms the custom filter structure or exclude structure into Q instances which can be directory used within Django methods .filter() | .exclude()

## Queries developed
### How to use the query builder
The structure of the querying has some rules to be followed to work properly. Firstly atleast and only 1 selector for each query must always be defined, however there can be as much modifiers and filters as you wish for example `person.where(age=40, age=70).where(age=50).sort_by('age').lazy().get()`, this is acceptable as it has only 1 selector method, however something like this is unacceptable `person.where(age=40, age=70).get().first()` 

Second the order of selectors, modifiters and selectors must always be sequentially `person.FILTER.MODIFIER.SELECTOR` for example `person.where(age=40).where(age=60).where(age__lt=30).order_by('age').lazy().get()` this is acceptable as it starts with all the filters, then modifiers and finally a selector, however something like this is unacceptable `person.lazy().where(age=50).where(age=60).get()`

### Selectors
Selectors are used to GET the data after the modifers and filters have been defined, however we can define certain queries to adjust the data gained from the database for example `first()`, only gets the first record, `all()` gets all the records regaurdless of the filters, `get()` gets all the data with filters and modifiers, etc.

- `get()`: The default selector that is used, if other properties are applied on the query such as modifiers and filters so for example don't do this
`where(age=40).all()` do this `where(age=40).get()`
- `first()`: The first selector will gain a single WKRI instead of a list of WKRI and gets the first resource for example `person.first()` or `person.where(age__greater_than=40).first()`, etc.
- `offset()`: The offset selector is used to grab a range of resources within the database for instance 
`person.where(age__less_than=40).offset(limit=20, offset=4)` which in turn grabs a range of resources
- `all()`: The all selector is used to grab all the records, this is not compatible with filters as get should be used instead so only `person.all()` or you can use modifiers `person.order_by('-age').all()`
- `find()`: The find selector gains a single resource, you must pass the resource instance ID into the find and this will return a single WKRI instance for example `person.find('036ce32f-325e-4533-8313-87936580ed25')`

### Modifiers
Modifiers are used to adjust query results by altering data in specific columns, changing the order of results, or optimizing performance. They help refine searches, improve efficiency, and ensure only relevant data is retrieved when needed. For example, lazy() can enhance performance by loading data only when required.

- `order_by('age')`: Applies the order by of the tile data based on the column name provided. We can control the ASC of data by just including the column name `order_by('age')` and the DESC of the data by including a '-', infront of the column name `order_by('-age')`. We can have mutplie order bys for example `order_by('age', '-bod')`.
- `order_by('-resourceinstance__createdtime')` & `order_by('-resourceinstance__createdtime')`: As tile data doesn't have a timestamp within the datatable. I also created a way to order the tile data based on the resourceinstance, in this example I'm using the resource instance timestamp to order the tile data


### Filters
Filters are used to refine query results by including or excluding specific data based on conditions. They help narrow down the dataset to meet specific criteria. For example, using age__gt=40 retrieves records where the age field in the database is greater than 40.

- `where(OPERATION=VALUE, OPERATION=VALUE)`: Applies a operation towards a value to filter out the data, please keep in mind you can chain mutplie where together `where().where()` or apply all the condictions inside 1 where statement `where(OPERATION=VALUE, OPERATION=VALUE)`, however either way, the where statement can only do AND as a logical operation
- `or_where(OPERATION=VALUE, OPERATION=VALUE)`: Applies a operation towards a value to filter out the data, please keep in mind you can chain mutplie or wheres together `where().or_where().or_where` or apply all the condictions inside 1 or where statement `or_where(OPERATION=VALUE, OPERATION=VALUE)`, however anything inside the `or_where()` is only AND logical operation. Moreover, if the statement was `where(age=40).or_where(age__gt=50, age__lt=60)`, it would look like this (age == 40 or (age > 50 and age < 60>))

There is also operations which can be preformed on these queries, [config](./config.py). Here are some listed below:
- **Greater than**: `__gt` | `__greater_than`  
- **Less than**: `__lt` | `__less_than`  
- **Greater than or equal to**: `__gte` | `__greater_than_or_equal`  