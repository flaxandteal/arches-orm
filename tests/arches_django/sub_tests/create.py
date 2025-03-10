import uuid
import random
from tests.utilities.seeders.seeder import Seeder
from tests.utilities.seeders.default.config import PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH, ACTIVITY_DATATYPE_NODE_ALIAS_KEYS, ACTIVITY_DEFAULT_SEED_PATH

def sub_test_create(arches_orm):
    instance_arches_orm_model_person = arches_orm.models.Person


    instance_arches_orm_model_activity = arches_orm.models.Activity
    instance_activity_seeder = Seeder(instance_arches_orm_model_activity, ACTIVITY_DATATYPE_NODE_ALIAS_KEYS, ACTIVITY_DEFAULT_SEED_PATH)

    instance_person_seeder = Seeder(instance_arches_orm_model_person, PERSON_DATATYPE_NODE_ALIAS_KEYS, PERSON_DEFAULT_SEED_PATH)
    sub_test_create_datatypes(instance_arches_orm_model_person, instance_person_seeder, instance_arches_orm_model_activity, instance_activity_seeder)

def sub_test_create_datatypes(instance_arches_orm_model_person, instance_person_seeder, instance_arches_orm_model_activity, instance_activity_seeder):
    def _string_datatype():
        keyword = "Asha"
        person = instance_arches_orm_model_person.create();
        person.family_members.pet = keyword
        person.save()
        reloaded_person = instance_arches_orm_model_person.find(person.id)
        print(instance_person_seeder.get_nested_datatype_value(reloaded_person, 'string'))
        assert(instance_person_seeder.get_nested_datatype_value(reloaded_person, 'string') == keyword)

    def _number_datatype():
        keyword = 613
        person = instance_arches_orm_model_person.create();
        person.system_reference_numbers.primaryreferencenumber.primary_reference_number = keyword
        person.save()
        reloaded_person = instance_arches_orm_model_person.find(person.id)
        assert(instance_person_seeder.get_nested_datatype_value(reloaded_person, 'number') == keyword)

    def _boolean_datatype():
        keyword = True
        person = instance_arches_orm_model_person.create();
        person.family_members.cars = keyword
        person.save()
        reloaded_person = instance_arches_orm_model_person.find(person.id)
        assert(instance_person_seeder.get_nested_datatype_value(reloaded_person, 'boolean') == keyword)

    def _date_datatype():
        keyword = '2000-04-15'
        person = instance_arches_orm_model_person.create();
        person.audit_metadata.audit_creation.creation_timespan.creation_end_date = keyword
        person.save()
        reloaded_person = instance_arches_orm_model_person.find(person.id)
        print(instance_person_seeder.get_nested_datatype_value(reloaded_person, 'date'))
        value = instance_person_seeder.get_nested_datatype_value(reloaded_person, 'date')
        assert keyword in str(value)

    def _concept_value():
        activity = instance_arches_orm_model_activity.create()
        record_status = activity.record_status_assignment.record_status
        StatusEnum = record_status.__collection__

        activity.record_status_assignment.record_status = StatusEnum.BacklogDashSkeleton
        assert activity.record_status_assignment.record_status == StatusEnum.BacklogDashSkeleton
        activity.save()
        found = instance_arches_orm_model_activity.find(activity.id)
        print(found.record_status_assignment.record_status)
        print(StatusEnum.BacklogDashSkeleton)


    _string_datatype()
    _number_datatype()
    _boolean_datatype()
    _date_datatype()
    _concept_value()
