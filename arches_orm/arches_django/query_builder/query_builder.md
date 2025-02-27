# Welcome to the Query Builder documents



## The folder/file structure


## How to use the query builder


## Queries developed
### Selectors
Selectors are used to GET the data after the modifers and filters have been defined, however we can define certain queries to adjust the data gained from the database for example `first()`, only gets the first record, `all()` gets all the records regaurdless of the filters, `get()` gets all the data with filters and modifiers, etc.

- `get()`: 
- `first()`:
- `offset()`:
- `all()`:
- `find()`:

### Modifiers
Modifiers are used to adjust query results by altering data in specific columns, changing the order of results, or optimizing performance. They help refine searches, improve efficiency, and ensure only relevant data is retrieved when needed. For example, lazy() can enhance performance by loading data only when required.

- `order_by('age')`: Applies the order by of the tile data based on the column name provided. We can control the ASC of data by just including the column name `order_by('age')` and the DESC of the data by including a '-', infront of the column name `order_by('-age')`. We can have mutplie order bys for example `order_by('age', '-bod')`.
- `lazy()`: Only loads the tile data UUID and maps this data, therefore it's faster speed as we don't have to apply a pseudo node class as this only gets converted if the user tries to access the pseudo node class.


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

Currently the filters can only handle certain datatypes where are listed below:
- String
- Number
- Boolean
- Date

Planning on creating compatible data types with the datatypes listed below:
- Domain value
- Concept value