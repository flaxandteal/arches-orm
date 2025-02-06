from arches_orm.view_models import SemanticViewModel

def assert_datatype_semmantic(value: any):
    assert(isinstance(value, SemanticViewModel))
