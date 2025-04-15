from arches_orm.pseudo_node.datatypes._register import ViewModelRegister

def _datatype_factory():
    """Caching datatype factory retrieval (possibly unnecessary)."""
    from arches.app.datatypes.datatypes import (
        DataTypeFactory,
        ResourceInstanceListDataType,
    )

    class DataTypeFactoryWithResourceInstanceList(DataTypeFactory):
        def get_instance(self, datatype):
            if datatype == "resource-instance-list":
                if (
                    "ResourceInstanceListDataType"
                    not in DataTypeFactory._datatype_instances
                ):
                    super().get_instance("resource-instance-list")
                    d_datatype = DataTypeFactory._datatypes[
                        "resource-instance-list"
                    ]
                    DataTypeFactory._datatype_instances[
                        "ResourceInstanceListDataType"
                    ] = ResourceInstanceListDataType(d_datatype)
                return DataTypeFactory._datatype_instances[
                    "ResourceInstanceListDataType"
                ]
            return super().get_instance(datatype)

    return DataTypeFactoryWithResourceInstanceList()

REGISTER = ViewModelRegister.create_with_factory(_datatype_factory())

def get_view_model_for_datatype(tile, node, parent, parent_cls, child_nodes, value=None):
    return REGISTER.make(
        tile, node, value=value, parent=parent, parent_cls=parent_cls, child_nodes=child_nodes
    )
