# Module arches_orm.arches_django.datatypes.user

??? example "View Source"

        import uuid

        from typing import Any, Callable

        from functools import cached_property

        from django.contrib.auth.models import User

        from arches.app.models.models import Node, ResourceInstance

        from arches.app.models.tile import Tile

        from arches.app.models.resource import Resource

        from collections import UserDict

        from arches_orm.view_models import (

            WKRI,

            UserViewModelMixin,

            UserProtocol,

            StringViewModel,

            RelatedResourceInstanceListViewModel,

            RelatedResourceInstanceViewModelMixin,

            ConceptListValueViewModel,

            ConceptValueViewModel,

            SemanticViewModel,

        )

        from ._register import REGISTER

        

        class UserViewModel(User, UserViewModelMixin):

            class Meta:

                proxy = True

                app_label = "arches-orm"

                db_table = User.objects.model._meta.db_table

        

        @REGISTER("user")

        def user(tile, node, value, _, __, user_datatype) -> UserProtocol:

            user = None

            value = value or tile.data.get(str(node.nodeid))

            if value:

                if isinstance(value, User):

                    if value.pk:

                        value = value.pk

                    else:

                        user = UserViewModel()

                        user.__dict__.update(value.__dict__)

                if value:

                    user = UserViewModel.objects.get(pk=int(value))

            if not user:

                user = UserViewModel()

            return user

        

        @user.as_tile_data

        def u_as_tile_data(view_model):

            return view_model.pk

## Variables

```python3
u_as_tile_data
```

## Classes

### UserViewModel

```python3
class UserViewModel(
    *args,
    **kwargs
)
```

UserViewModel(id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)

??? example "View Source"
        class UserViewModel(User, UserViewModelMixin):

            class Meta:

                proxy = True

                app_label = "arches-orm"

                db_table = User.objects.model._meta.db_table

------

#### Ancestors (in MRO)

* django.contrib.auth.models.User
* django.contrib.auth.models.AbstractUser
* django.contrib.auth.base_user.AbstractBaseUser
* django.contrib.auth.models.PermissionsMixin
* django.db.models.base.Model
* django.db.models.utils.AltersData
* arches_orm.view_models.UserViewModelMixin
* arches_orm.view_models.ViewModel

#### Class variables

```python3
DoesNotExist
```

```python3
EMAIL_FIELD
```

```python3
Meta
```

```python3
MultipleObjectsReturned
```

```python3
REQUIRED_FIELDS
```

```python3
USERNAME_FIELD
```

```python3
externaloauthtoken_set
```

```python3
graphxpublishedgraph_set
```

```python3
groups
```

```python3
loadevent_set
```

```python3
objects
```

```python3
searchexporthistory_set
```

```python3
user_permissions
```

```python3
username_validator
```

```python3
userobjectpermission_set
```

```python3
userprofile
```

```python3
userxnotification_set
```

```python3
userxnotificationtype_set
```

```python3
userxtask_set
```

```python3
workflowhistory_set
```

#### Static methods

    
#### check

```python3
def check(
    **kwargs
)
```

??? example "View Source"
            @classmethod

            def check(cls, **kwargs):

                errors = [

                    *cls._check_swappable(),

                    *cls._check_model(),

                    *cls._check_managers(**kwargs),

                ]

                if not cls._meta.swapped:

                    databases = kwargs.get("databases") or []

                    errors += [

                        *cls._check_fields(**kwargs),

                        *cls._check_m2m_through_same_relationship(),

                        *cls._check_long_column_names(databases),

                    ]

                    clash_errors = (

                        *cls._check_id_field(),

                        *cls._check_field_name_clashes(),

                        *cls._check_model_name_db_lookup_clashes(),

                        *cls._check_property_name_related_field_accessor_clashes(),

                        *cls._check_single_primary_key(),

                    )

                    errors.extend(clash_errors)

                    # If there are field name clashes, hide consequent column name

                    # clashes.

                    if not clash_errors:

                        errors.extend(cls._check_column_name_clashes())

                    errors += [

                        *cls._check_index_together(),

                        *cls._check_unique_together(),

                        *cls._check_indexes(databases),

                        *cls._check_ordering(),

                        *cls._check_constraints(databases),

                        *cls._check_default_pk(),

                        *cls._check_db_table_comment(databases),

                    ]

                return errors

    
#### from_db

```python3
def from_db(
    db,
    field_names,
    values
)
```

??? example "View Source"
            @classmethod

            def from_db(cls, db, field_names, values):

                if len(values) != len(cls._meta.concrete_fields):

                    values_iter = iter(values)

                    values = [

                        next(values_iter) if f.attname in field_names else DEFERRED

                        for f in cls._meta.concrete_fields

                    ]

                new = cls(*values)

                new._state.adding = False

                new._state.db = db

                return new

    
#### get_anonymous

```python3
def get_anonymous(
    
)
```

??? example "View Source"
            setattr(User, 'get_anonymous', staticmethod(lambda: get_anonymous_user()))

    
#### get_email_field_name

```python3
def get_email_field_name(
    
)
```

??? example "View Source"
            @classmethod

            def get_email_field_name(cls):

                try:

                    return cls.EMAIL_FIELD

                except AttributeError:

                    return "email"

    
#### normalize_username

```python3
def normalize_username(
    username
)
```

??? example "View Source"
            @classmethod

            def normalize_username(cls, username):

                return (

                    unicodedata.normalize("NFKC", username)

                    if isinstance(username, str)

                    else username

                )

#### Instance variables

```python3
is_anonymous
```

Always return False. This is a way of comparing User objects to

anonymous users.

```python3
is_authenticated
```

Always return True. This is a way to tell if the user has been

authenticated in templates.

```python3
pk
```

#### Methods

    
#### add_obj_perm

```python3
def add_obj_perm(
    self,
    perm,
    obj
)
```

??? example "View Source"
                    lambda self, perm, obj: UserObjectPermission.objects.assign_perm(perm, self, obj))

    
#### adelete

```python3
def adelete(
    self,
    using=None,
    keep_parents=False
)
```

??? example "View Source"
            async def adelete(self, using=None, keep_parents=False):

                return await sync_to_async(self.delete)(

                    using=using,

                    keep_parents=keep_parents,

                )

    
#### arefresh_from_db

```python3
def arefresh_from_db(
    self,
    using=None,
    fields=None
)
```

??? example "View Source"
            async def arefresh_from_db(self, using=None, fields=None):

                return await sync_to_async(self.refresh_from_db)(using=using, fields=fields)

    
#### asave

```python3
def asave(
    self,
    force_insert=False,
    force_update=False,
    using=None,
    update_fields=None
)
```

??? example "View Source"
            async def asave(

                self, force_insert=False, force_update=False, using=None, update_fields=None

            ):

                return await sync_to_async(self.save)(

                    force_insert=force_insert,

                    force_update=force_update,

                    using=using,

                    update_fields=update_fields,

                )

    
#### check_password

```python3
def check_password(
    self,
    raw_password
)
```

Return a boolean of whether the raw_password was correct. Handles

hashing formats behind the scenes.

??? example "View Source"
            def check_password(self, raw_password):

                """

                Return a boolean of whether the raw_password was correct. Handles

                hashing formats behind the scenes.

                """

                def setter(raw_password):

                    self.set_password(raw_password)

                    # Password hash upgrades shouldn't be considered password changes.

                    self._password = None

                    self.save(update_fields=["password"])

                return check_password(raw_password, self.password, setter)

    
#### clean

```python3
def clean(
    self
)
```

Hook for doing any extra model-wide validation after clean() has been

called on every field by self.clean_fields. Any ValidationError raised
by this method will not be associated with a particular field; it will
have a special-case association with the field defined by NON_FIELD_ERRORS.

??? example "View Source"
            def clean(self):

                super().clean()

                self.email = self.__class__.objects.normalize_email(self.email)

    
#### clean_fields

```python3
def clean_fields(
    self,
    exclude=None
)
```

Clean all fields and raise a ValidationError containing a dict

of all validation errors if any occur.

??? example "View Source"
            def clean_fields(self, exclude=None):

                """

                Clean all fields and raise a ValidationError containing a dict

                of all validation errors if any occur.

                """

                if exclude is None:

                    exclude = set()

                errors = {}

                for f in self._meta.fields:

                    if f.name in exclude:

                        continue

                    # Skip validation for empty fields with blank=True. The developer

                    # is responsible for making sure they have a valid value.

                    raw_value = getattr(self, f.attname)

                    if f.blank and raw_value in f.empty_values:

                        continue

                    try:

                        setattr(self, f.attname, f.clean(raw_value, self))

                    except ValidationError as e:

                        errors[f.name] = e.error_list

                if errors:

                    raise ValidationError(errors)

    
#### date_error_message

```python3
def date_error_message(
    self,
    lookup_type,
    field_name,
    unique_for
)
```

??? example "View Source"
            def date_error_message(self, lookup_type, field_name, unique_for):

                opts = self._meta

                field = opts.get_field(field_name)

                return ValidationError(

                    message=field.error_messages["unique_for_date"],

                    code="unique_for_date",

                    params={

                        "model": self,

                        "model_name": capfirst(opts.verbose_name),

                        "lookup_type": lookup_type,

                        "field": field_name,

                        "field_label": capfirst(field.verbose_name),

                        "date_field": unique_for,

                        "date_field_label": capfirst(opts.get_field(unique_for).verbose_name),

                    },

                )

    
#### date_joined

```python3
def date_joined(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### del_obj_perm

```python3
def del_obj_perm(
    self,
    perm,
    obj
)
```

??? example "View Source"
                    lambda self, perm, obj: UserObjectPermission.objects.remove_perm(perm, self, obj))

    
#### delete

```python3
def delete(
    self,
    using=None,
    keep_parents=False
)
```

??? example "View Source"
            def delete(self, using=None, keep_parents=False):

                if self.pk is None:

                    raise ValueError(

                        "%s object can't be deleted because its %s attribute is set "

                        "to None." % (self._meta.object_name, self._meta.pk.attname)

                    )

                using = using or router.db_for_write(self.__class__, instance=self)

                collector = Collector(using=using, origin=self)

                collector.collect([self], keep_parents=keep_parents)

                return collector.delete()

    
#### email

```python3
def email(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### email_user

```python3
def email_user(
    self,
    subject,
    message,
    from_email=None,
    **kwargs
)
```

Send an email to this user.

??? example "View Source"
            def email_user(self, subject, message, from_email=None, **kwargs):

                """Send an email to this user."""

                send_mail(subject, message, from_email, [self.email], **kwargs)

    
#### evict_obj_perms_cache

```python3
def evict_obj_perms_cache(
    obj
)
```

??? example "View Source"
        def evict_obj_perms_cache(obj):

            if hasattr(obj, '_guardian_perms_cache'):

                delattr(obj, '_guardian_perms_cache')

                return True

            return False

    
#### first_name

```python3
def first_name(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### full_clean

```python3
def full_clean(
    self,
    exclude=None,
    validate_unique=True,
    validate_constraints=True
)
```

Call clean_fields(), clean(), validate_unique(), and

validate_constraints() on the model. Raise a ValidationError for any
errors that occur.

??? example "View Source"
            def full_clean(self, exclude=None, validate_unique=True, validate_constraints=True):

                """

                Call clean_fields(), clean(), validate_unique(), and

                validate_constraints() on the model. Raise a ValidationError for any

                errors that occur.

                """

                errors = {}

                if exclude is None:

                    exclude = set()

                else:

                    exclude = set(exclude)

                try:

                    self.clean_fields(exclude=exclude)

                except ValidationError as e:

                    errors = e.update_error_dict(errors)

                # Form.clean() is run even if other validation fails, so do the

                # same with Model.clean() for consistency.

                try:

                    self.clean()

                except ValidationError as e:

                    errors = e.update_error_dict(errors)

                # Run unique checks, but only for fields that passed validation.

                if validate_unique:

                    for name in errors:

                        if name != NON_FIELD_ERRORS and name not in exclude:

                            exclude.add(name)

                    try:

                        self.validate_unique(exclude=exclude)

                    except ValidationError as e:

                        errors = e.update_error_dict(errors)

                # Run constraints checks, but only for fields that passed validation.

                if validate_constraints:

                    for name in errors:

                        if name != NON_FIELD_ERRORS and name not in exclude:

                            exclude.add(name)

                    try:

                        self.validate_constraints(exclude=exclude)

                    except ValidationError as e:

                        errors = e.update_error_dict(errors)

                if errors:

                    raise ValidationError(errors)

    
#### get_all_permissions

```python3
def get_all_permissions(
    self,
    obj=None
)
```

??? example "View Source"
            def get_all_permissions(self, obj=None):

                return _user_get_permissions(self, obj, "all")

    
#### get_constraints

```python3
def get_constraints(
    self
)
```

??? example "View Source"
            def get_constraints(self):

                constraints = [(self.__class__, self._meta.constraints)]

                for parent_class in self._meta.get_parent_list():

                    if parent_class._meta.constraints:

                        constraints.append((parent_class, parent_class._meta.constraints))

                return constraints

    
#### get_deferred_fields

```python3
def get_deferred_fields(
    self
)
```

Return a set containing names of deferred fields for this instance.

??? example "View Source"
            def get_deferred_fields(self):

                """

                Return a set containing names of deferred fields for this instance.

                """

                return {

                    f.attname

                    for f in self._meta.concrete_fields

                    if f.attname not in self.__dict__

                }

    
#### get_full_name

```python3
def get_full_name(
    self
)
```

Return the first_name plus the last_name, with a space in between.

??? example "View Source"
            def get_full_name(self):

                """

                Return the first_name plus the last_name, with a space in between.

                """

                full_name = "%s %s" % (self.first_name, self.last_name)

                return full_name.strip()

    
#### get_group_permissions

```python3
def get_group_permissions(
    self,
    obj=None
)
```

Return a list of permission strings that this user has through their

groups. Query all available auth backends. If an object is passed in,
return only permissions matching this object.

??? example "View Source"
            def get_group_permissions(self, obj=None):

                """

                Return a list of permission strings that this user has through their

                groups. Query all available auth backends. If an object is passed in,

                return only permissions matching this object.

                """

                return _user_get_permissions(self, obj, "group")

    
#### get_next_by_date_joined

```python3
def get_next_by_date_joined(
    self,
    *,
    field=<django.db.models.fields.DateTimeField: date_joined>,
    is_next=True,
    **kwargs
)
```

??? example "View Source"
                def _method(cls_or_self, /, *args, **keywords):

                    keywords = {**self.keywords, **keywords}

                    return self.func(cls_or_self, *self.args, *args, **keywords)

    
#### get_previous_by_date_joined

```python3
def get_previous_by_date_joined(
    self,
    *,
    field=<django.db.models.fields.DateTimeField: date_joined>,
    is_next=False,
    **kwargs
)
```

??? example "View Source"
                def _method(cls_or_self, /, *args, **keywords):

                    keywords = {**self.keywords, **keywords}

                    return self.func(cls_or_self, *self.args, *args, **keywords)

    
#### get_session_auth_fallback_hash

```python3
def get_session_auth_fallback_hash(
    self
)
```

??? example "View Source"
            def get_session_auth_fallback_hash(self):

                for fallback_secret in settings.SECRET_KEY_FALLBACKS:

                    yield self._get_session_auth_hash(secret=fallback_secret)

    
#### get_session_auth_hash

```python3
def get_session_auth_hash(
    self
)
```

Return an HMAC of the password field.

??? example "View Source"
            def get_session_auth_hash(self):

                """

                Return an HMAC of the password field.

                """

                return self._get_session_auth_hash()

    
#### get_short_name

```python3
def get_short_name(
    self
)
```

Return the short name for the user.

??? example "View Source"
            def get_short_name(self):

                """Return the short name for the user."""

                return self.first_name

    
#### get_user_permissions

```python3
def get_user_permissions(
    self,
    obj=None
)
```

Return a list of permission strings that this user has directly.

Query all available auth backends. If an object is passed in,
return only permissions matching this object.

??? example "View Source"
            def get_user_permissions(self, obj=None):

                """

                Return a list of permission strings that this user has directly.

                Query all available auth backends. If an object is passed in,

                return only permissions matching this object.

                """

                return _user_get_permissions(self, obj, "user")

    
#### get_username

```python3
def get_username(
    self
)
```

Return the username for this User.

??? example "View Source"
            def get_username(self):

                """Return the username for this User."""

                return getattr(self, self.USERNAME_FIELD)

    
#### has_module_perms

```python3
def has_module_perms(
    self,
    app_label
)
```

Return True if the user has any permissions in the given app label.

Use similar logic as has_perm(), above.

??? example "View Source"
            def has_module_perms(self, app_label):

                """

                Return True if the user has any permissions in the given app label.

                Use similar logic as has_perm(), above.

                """

                # Active superusers have all permissions.

                if self.is_active and self.is_superuser:

                    return True

                return _user_has_module_perms(self, app_label)

    
#### has_perm

```python3
def has_perm(
    self,
    perm,
    obj=None
)
```

Return True if the user has the specified permission. Query all

available auth backends, but return immediately if any backend returns
True. Thus, a user who has permission from a single auth backend is
assumed to have permission in general. If an object is provided, check
permissions for that object.

??? example "View Source"
            def has_perm(self, perm, obj=None):

                """

                Return True if the user has the specified permission. Query all

                available auth backends, but return immediately if any backend returns

                True. Thus, a user who has permission from a single auth backend is

                assumed to have permission in general. If an object is provided, check

                permissions for that object.

                """

                # Active superusers have all permissions.

                if self.is_active and self.is_superuser:

                    return True

                # Otherwise we need to check the backends.

                return _user_has_perm(self, perm, obj)

    
#### has_perms

```python3
def has_perms(
    self,
    perm_list,
    obj=None
)
```

Return True if the user has each of the specified permissions. If

object is passed, check if the user has all required perms for it.

??? example "View Source"
            def has_perms(self, perm_list, obj=None):

                """

                Return True if the user has each of the specified permissions. If

                object is passed, check if the user has all required perms for it.

                """

                if not is_iterable(perm_list) or isinstance(perm_list, str):

                    raise ValueError("perm_list must be an iterable of permissions.")

                return all(self.has_perm(perm, obj) for perm in perm_list)

    
#### has_usable_password

```python3
def has_usable_password(
    self
)
```

Return False if set_unusable_password() has been called for this user.

??? example "View Source"
            def has_usable_password(self):

                """

                Return False if set_unusable_password() has been called for this user.

                """

                return is_password_usable(self.password)

    
#### id

```python3
def id(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### is_active

```python3
def is_active(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### is_staff

```python3
def is_staff(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### is_superuser

```python3
def is_superuser(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### last_login

```python3
def last_login(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### last_name

```python3
def last_name(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### natural_key

```python3
def natural_key(
    self
)
```

??? example "View Source"
            def natural_key(self):

                return (self.get_username(),)

    
#### password

```python3
def password(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### prepare_database_save

```python3
def prepare_database_save(
    self,
    field
)
```

??? example "View Source"
            def prepare_database_save(self, field):

                if self.pk is None:

                    raise ValueError(

                        "Unsaved model instance %r cannot be used in an ORM query." % self

                    )

                return getattr(self, field.remote_field.get_related_field().attname)

    
#### refresh_from_db

```python3
def refresh_from_db(
    self,
    using=None,
    fields=None
)
```

Reload field values from the database.

By default, the reloading happens from the database this instance was
loaded from, or by the read router if this instance wasn't loaded from
any database. The using parameter will override the default.

Fields can be used to specify which fields to reload. The fields
should be an iterable of field attnames. If fields is None, then
all non-deferred fields are reloaded.

When accessing deferred fields of an instance, the deferred loading
of the field will call this method.

??? example "View Source"
            def refresh_from_db(self, using=None, fields=None):

                """

                Reload field values from the database.

                By default, the reloading happens from the database this instance was

                loaded from, or by the read router if this instance wasn't loaded from

                any database. The using parameter will override the default.

                Fields can be used to specify which fields to reload. The fields

                should be an iterable of field attnames. If fields is None, then

                all non-deferred fields are reloaded.

                When accessing deferred fields of an instance, the deferred loading

                of the field will call this method.

                """

                if fields is None:

                    self._prefetched_objects_cache = {}

                else:

                    prefetched_objects_cache = getattr(self, "_prefetched_objects_cache", ())

                    for field in fields:

                        if field in prefetched_objects_cache:

                            del prefetched_objects_cache[field]

                            fields.remove(field)

                    if not fields:

                        return

                    if any(LOOKUP_SEP in f for f in fields):

                        raise ValueError(

                            'Found "%s" in fields argument. Relations and transforms '

                            "are not allowed in fields." % LOOKUP_SEP

                        )

                hints = {"instance": self}

                db_instance_qs = self.__class__._base_manager.db_manager(

                    using, hints=hints

                ).filter(pk=self.pk)

                # Use provided fields, if not set then reload all non-deferred fields.

                deferred_fields = self.get_deferred_fields()

                if fields is not None:

                    fields = list(fields)

                    db_instance_qs = db_instance_qs.only(*fields)

                elif deferred_fields:

                    fields = [

                        f.attname

                        for f in self._meta.concrete_fields

                        if f.attname not in deferred_fields

                    ]

                    db_instance_qs = db_instance_qs.only(*fields)

                db_instance = db_instance_qs.get()

                non_loaded_fields = db_instance.get_deferred_fields()

                for field in self._meta.concrete_fields:

                    if field.attname in non_loaded_fields:

                        # This field wasn't refreshed - skip ahead.

                        continue

                    setattr(self, field.attname, getattr(db_instance, field.attname))

                    # Clear cached foreign keys.

                    if field.is_relation and field.is_cached(self):

                        field.delete_cached_value(self)

                # Clear cached relations.

                for field in self._meta.related_objects:

                    if field.is_cached(self):

                        field.delete_cached_value(self)

                # Clear cached private relations.

                for field in self._meta.private_fields:

                    if field.is_relation and field.is_cached(self):

                        field.delete_cached_value(self)

                self._state.db = db_instance._state.db

    
#### save

```python3
def save(
    self,
    *args,
    **kwargs
)
```

Save the current instance. Override this in a subclass if you want to

control the saving process.

The 'force_insert' and 'force_update' parameters can be used to insist
that the "save" must be an SQL insert or update (or equivalent for
non-SQL backends), respectively. Normally, they should not be set.

??? example "View Source"
            def save(self, *args, **kwargs):

                super().save(*args, **kwargs)

                if self._password is not None:

                    password_validation.password_changed(self._password, self)

                    self._password = None

    
#### save_base

```python3
def save_base(
    self,
    raw=False,
    force_insert=False,
    force_update=False,
    using=None,
    update_fields=None
)
```

Handle the parts of saving which should be done only once per save,

yet need to be done in raw saves, too. This includes some sanity
checks and signal sending.

The 'raw' argument is telling save_base not to save any parent
models and not to do any changes to the values before save. This
is used by fixture loading.

??? example "View Source"
            def save_base(

                self,

                raw=False,

                force_insert=False,

                force_update=False,

                using=None,

                update_fields=None,

            ):

                """

                Handle the parts of saving which should be done only once per save,

                yet need to be done in raw saves, too. This includes some sanity

                checks and signal sending.

                The 'raw' argument is telling save_base not to save any parent

                models and not to do any changes to the values before save. This

                is used by fixture loading.

                """

                using = using or router.db_for_write(self.__class__, instance=self)

                assert not (force_insert and (force_update or update_fields))

                assert update_fields is None or update_fields

                cls = origin = self.__class__

                # Skip proxies, but keep the origin as the proxy model.

                if cls._meta.proxy:

                    cls = cls._meta.concrete_model

                meta = cls._meta

                if not meta.auto_created:

                    pre_save.send(

                        sender=origin,

                        instance=self,

                        raw=raw,

                        using=using,

                        update_fields=update_fields,

                    )

                # A transaction isn't needed if one query is issued.

                if meta.parents:

                    context_manager = transaction.atomic(using=using, savepoint=False)

                else:

                    context_manager = transaction.mark_for_rollback_on_error(using=using)

                with context_manager:

                    parent_inserted = False

                    if not raw:

                        parent_inserted = self._save_parents(cls, using, update_fields)

                    updated = self._save_table(

                        raw,

                        cls,

                        force_insert or parent_inserted,

                        force_update,

                        using,

                        update_fields,

                    )

                # Store the database on which the object was saved

                self._state.db = using

                # Once saved, this is no longer a to-be-added instance.

                self._state.adding = False

                # Signal that the save is complete

                if not meta.auto_created:

                    post_save.send(

                        sender=origin,

                        instance=self,

                        created=(not updated),

                        update_fields=update_fields,

                        raw=raw,

                        using=using,

                    )

    
#### serializable_value

```python3
def serializable_value(
    self,
    field_name
)
```

Return the value of the field name for this instance. If the field is

a foreign key, return the id value instead of the object. If there's
no Field object with this name on the model, return the model
attribute's value.

Used to serialize a field's value (in the serializer, or form output,
for example). Normally, you would just access the attribute directly
and not use this method.

??? example "View Source"
            def serializable_value(self, field_name):

                """

                Return the value of the field name for this instance. If the field is

                a foreign key, return the id value instead of the object. If there's

                no Field object with this name on the model, return the model

                attribute's value.

                Used to serialize a field's value (in the serializer, or form output,

                for example). Normally, you would just access the attribute directly

                and not use this method.

                """

                try:

                    field = self._meta.get_field(field_name)

                except FieldDoesNotExist:

                    return getattr(self, field_name)

                return getattr(self, field.attname)

    
#### set_password

```python3
def set_password(
    self,
    raw_password
)
```

??? example "View Source"
            def set_password(self, raw_password):

                self.password = make_password(raw_password)

                self._password = raw_password

    
#### set_unusable_password

```python3
def set_unusable_password(
    self
)
```

??? example "View Source"
            def set_unusable_password(self):

                # Set a value that will never be a valid hash

                self.password = make_password(None)

    
#### unique_error_message

```python3
def unique_error_message(
    self,
    model_class,
    unique_check
)
```

??? example "View Source"
            def unique_error_message(self, model_class, unique_check):

                opts = model_class._meta

                params = {

                    "model": self,

                    "model_class": model_class,

                    "model_name": capfirst(opts.verbose_name),

                    "unique_check": unique_check,

                }

                # A unique field

                if len(unique_check) == 1:

                    field = opts.get_field(unique_check[0])

                    params["field_label"] = capfirst(field.verbose_name)

                    return ValidationError(

                        message=field.error_messages["unique"],

                        code="unique",

                        params=params,

                    )

                # unique_together

                else:

                    field_labels = [

                        capfirst(opts.get_field(f).verbose_name) for f in unique_check

                    ]

                    params["field_labels"] = get_text_list(field_labels, _("and"))

                    return ValidationError(

                        message=_("%(model_name)s with this %(field_labels)s already exists."),

                        code="unique_together",

                        params=params,

                    )

    
#### username

```python3
def username(
    ...
)
```

A wrapper for a deferred-loading field. When the value is read from this

object the first time, the query is executed.

    
#### validate_constraints

```python3
def validate_constraints(
    self,
    exclude=None
)
```

??? example "View Source"
            def validate_constraints(self, exclude=None):

                constraints = self.get_constraints()

                using = router.db_for_write(self.__class__, instance=self)

                errors = {}

                for model_class, model_constraints in constraints:

                    for constraint in model_constraints:

                        try:

                            constraint.validate(model_class, self, exclude=exclude, using=using)

                        except ValidationError as e:

                            if (

                                getattr(e, "code", None) == "unique"

                                and len(constraint.fields) == 1

                            ):

                                errors.setdefault(constraint.fields[0], []).append(e)

                            else:

                                errors = e.update_error_dict(errors)

                if errors:

                    raise ValidationError(errors)

    
#### validate_unique

```python3
def validate_unique(
    self,
    exclude=None
)
```

Check unique constraints on the model and raise ValidationError if any

failed.

??? example "View Source"
            def validate_unique(self, exclude=None):

                """

                Check unique constraints on the model and raise ValidationError if any

                failed.

                """

                unique_checks, date_checks = self._get_unique_checks(exclude=exclude)

                errors = self._perform_unique_checks(unique_checks)

                date_errors = self._perform_date_checks(date_checks)

                for k, v in date_errors.items():

                    errors.setdefault(k, []).extend(v)

                if errors:

                    raise ValidationError(errors)