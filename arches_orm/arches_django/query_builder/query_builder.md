# Welcome to the Query Builder system
The query builder purpose is to get WKRI with contained tile data which is wrapped around view_model classes. The query builder allows you to preform some queries on these WKRI with node alias, instead of using the entire node id as the node id is UUID and the node alias is a custom key. Since the fastest way to pull data from the database is to use the database tools, the query builder takes advantage of the builder pattern https://refactoring.guru/design-patterns/builder to build Django quries which intern build SQL quries.

The query builder quries are split up into 3 different sections:
- **Filters**: This is used filtering the data on the Django quries, therefore quries such as where(), or_where() would be considered filtering
- **Modifiers**: This is used towards modifying the records (So not removing but adjusting), therefore quries such as order_by(), lazy()
- **Selectors**: This is used towards selecting the records (So obtaining the data in a certain way), therefore quries such as get(), all(), first(), offset()

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
- `lazy()`: Only loads the tile data UUID and maps this data, therefore it's faster speed as we don't have to apply a pseudo node class as this only gets converted if the user tries to access the pseudo node class.
- `order_by('-resourceinstance__createdtime')` & `order_by('-resourceinstance__createdtime')`: As tile data doesn't have a timestamp within the datatable. I also created a way to order the tile data based on the resourceinstance, in this example I'm using the resource instance timestamp to order the tile data


### Filters
Filters are used to refine query results by including or excluding specific data based on conditions. They help narrow down the dataset to meet specific criteria. For example, using age__gt=40 retrieves records where the age field in the database is greater than 40.

- `where(OPERATION=VALUE, OPERATION=VALUE)`: Applies a operation towards a value to filter out the data, please keep in mind you can chain mutplie where together `where().where()` or apply all the condictions inside 1 where statement `where(OPERATION=VALUE, OPERATION=VALUE)`, however either way, the where statement can only do AND as a logical operation
- `or_where(OPERATION=VALUE, OPERATION=VALUE)`: Applies a operation towards a value to filter out the data, please keep in mind you can chain mutplie or wheres together `where().or_where().or_where` or apply all the condictions inside 1 or where statement `or_where(OPERATION=VALUE, OPERATION=VALUE)`, however anything inside the `or_where()` is only AND logical operation. Moreover, if the statement was `where(age=40).or_where(age__gt=50, age__lt=60)`, it would look like this (age == 40 or (age > 50 and age < 60>))

There is also operations which can be preformed on these queries, which you can view iniside .consts.py, however these are also listed below:
- **Greater than**: `__gt` | `__greater_than`  
- **Less than**: `__lt` | `__less_than`  
- **Greater than or equal to**: `__gte` | `__greater_than_or_equal`  
- **Less than or equal to**: `__lte` | `__less_than_or_equal`  
- **Not equal**: `__ne` | `__not_equal`  
- **Insensitive contains**: `__ict` | `__icontains`  
- **Insensitive starts with**: `__istartswith` | `__isw`  
- **Starts with**: `__startswith` | `__sw`  
- **Contains**: `__ct` | `__contains`  