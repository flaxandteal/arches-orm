--- Licensed AGPL as from ARCHES (TODO: tidy license string)

INSERT INTO languages(code, name, default_direction, scope, isdefault) VALUES ('en-US', 'ENGLISH', 'rtl', 'system', true);
INSERT INTO languages(code, name, default_direction, scope, isdefault) VALUES ('en', 'ENGLISH', 'rtl', 'system', true);
INSERT INTO languages(code, name, default_direction, scope, isdefault) VALUES ('fr', 'FRENCH', 'rtl', 'system', true);
INSERT INTO languages(code, name, default_direction, scope, isdefault) VALUES ('zh', 'CHINESE', 'rtl', 'system', true);
INSERT INTO languages(code, name, default_direction, scope, isdefault) VALUES ('de', 'GERMAN', 'rtl', 'system', true);
INSERT INTO languages(code, name, default_direction, scope, isdefault) VALUES ('pt', 'PORTUGUESE', 'rtl', 'system', true);
INSERT INTO languages(code, name, default_direction, scope, isdefault) VALUES ('ru', 'RUSSIAN', 'rtl', 'system', true);
INSERT INTO languages(code, name, default_direction, scope, isdefault) VALUES ('el', 'GREEK', 'rtl', 'system', true);

INSERT INTO report_templates(templateid, name, description, component, componentname, defaultconfig, preload_resource_data)
    VALUES ('50000000-0000-0000-0000-000000000001', 'No Header Template', 'Default Template', 'reports/default', 'default-report', '{}', 't');

INSERT INTO report_templates(templateid, name, description, component, componentname, defaultconfig, preload_resource_data)
    VALUES ('50000000-0000-0000-0000-000000000002', 'Map Header Template', 'Map Widget', 'reports/map', 'map-report', '{
        "basemap": "streets",
        "geometryTypes": [{"text":"Point", "id":"Point"}, {"text":"Line", "id":"Line"}, {"text":"Polygon", "id":"Polygon"}],
        "overlayConfigs": [],
        "overlayOpacity": 0.0,
        "geocodeProvider": "MapzenGeocoder",
        "zoom": 10,
        "maxZoom": 20,
        "minZoom": 0,
        "centerX": -122.3979693,
        "centerY": 37.79,
        "pitch": 0.0,
        "bearing": 0.0,
        "geocodePlaceholder": "Search",
        "geocoderVisible": true,
        "featureColor": null,
        "featureLineWidth": null,
        "featurePointSize": null,
        "featureEditingDisabled": true,
        "mapControlsHidden": false
    }', 't');

INSERT INTO report_templates(templateid, name, description, component, componentname, defaultconfig, preload_resource_data)
    VALUES ('50000000-0000-0000-0000-000000000003', 'Image Header Template', 'Image Header', 'reports/image', 'image-report', '{"nodes": []}', 't');
INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000001', 'text-widget', 'views/components/widgets/text', 'string', '{ "placeholder": "Enter text", "width": "100%", "maxLength": null}');


INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000002', 'concept-select-widget', 'views/components/widgets/concept-select', 'concept', '{ "placeholder": "Select an option", "options": [] }');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000012', 'concept-multiselect-widget', 'views/components/widgets/concept-multiselect', 'concept-list', '{ "placeholder": "Select an option", "options": [] }');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000015', 'domain-select-widget', 'views/components/widgets/domain-select', 'domain-value', '{ "placeholder": "Select an option" }');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000016', 'domain-multiselect-widget', 'views/components/widgets/domain-multiselect', 'domain-value-list', '{ "placeholder": "Select an option" }');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000003', 'switch-widget', 'views/components/widgets/switch', 'boolean', '{ "subtitle": "Click to switch"}');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000004', 'datepicker-widget', 'views/components/widgets/datepicker', 'date',
    '{
        "placeholder": "Enter date",
        "viewMode": "days",
        "dateFormat": "YYYY-MM-DD",
        "minDate": false,
        "maxDate": false
    }'
);

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000005', 'rich-text-widget', 'views/components/widgets/rich-text', 'string', '{}');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000006', 'radio-boolean-widget', 'views/components/widgets/radio-boolean', 'boolean', '{"trueLabel": "Yes", "falseLabel": "No"}');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000007', 'map-widget', 'views/components/widgets/map', 'geojson-feature-collection',
    '{
        "basemap": "streets",
        "geometryTypes": [{"text":"Point", "id":"Point"}, {"text":"Line", "id":"Line"}, {"text":"Polygon", "id":"Polygon"}],
        "overlayConfigs": [],
        "overlayOpacity": 0.0,
        "geocodeProvider": "MapzenGeocoder",
        "zoom": 0,
        "maxZoom": 20,
        "minZoom": 0,
        "centerX": 0,
        "centerY": 0,
        "pitch": 0.0,
        "bearing": 0.0,
        "geocodePlaceholder": "Search",
        "geocoderVisible": true,
        "featureColor": null,
        "featureLineWidth": null,
        "featurePointSize": null
    }'
);

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000008', 'number-widget', 'views/components/widgets/number', 'number', '{ "placeholder": "Enter number", "width": "100%", "min":"", "max":""}');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000009', 'concept-radio-widget', 'views/components/widgets/concept-radio', 'concept', '{ "options": [] }');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000013', 'concept-checkbox-widget', 'views/components/widgets/concept-checkbox', 'concept-list', '{ "options": [] }');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000017', 'domain-radio-widget', 'views/components/widgets/domain-radio', 'domain-value', '{}');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000018', 'domain-checkbox-widget', 'views/components/widgets/domain-checkbox', 'domain-value-list', '{}');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000019', 'file-widget', 'views/components/widgets/file', 'file-list', '{"acceptedFiles": "", "maxFilesize": "200"}');

INSERT INTO widgets(widgetid, name, component, datatype, defaultconfig)
    VALUES ('10000000-0000-0000-0000-000000000101', 'user', 'views/components/widgets/user', 'user', '{}');

INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('string', 'fa fa-file-code-o', 'datatypes.py', 'StringDataType',  null, null, null, FALSE, '10000000-0000-0000-0000-000000000001');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES (
    'user',
    'fa fa-location-arrow',
    'user.py',
    'UserDataType',
    null,
    null,
    null,
    FALSE,
    '10000000-0000-0000-0000-000000000101'
);
INSERT INTO widgets(
    widgetid,
    name,
    component,
    datatype,
    defaultconfig
) VALUES (
    '31f3728c-7613-11e7-a139-784f435179ea',
    'resource-instance-select-widget',
    'views/components/widgets/resource-instance-select',
    'resource-instance',
    '{
        "placeholder": ""
    }'
);

INSERT INTO d_data_types(
    datatype, iconclass, modulename,
    classname, defaultconfig, configcomponent,
    configname, isgeometric, defaultwidget,
    issearchable
) VALUES (
    'resource-instance',
    'fa fa-external-link-o',
    'datatypes.py',
    'ResourceInstanceDataType',
    '{
        "graphid": null
    }',
    'views/components/datatypes/resource-instance',
    'resource-instance-datatype-config',
    FALSE,
    '31f3728c-7613-11e7-a139-784f435179ea',
    TRUE
);

INSERT INTO widgets(
    widgetid,
    name,
    component,
    datatype,
    defaultconfig
) VALUES (
    'ff3c400a-76ec-11e7-a793-784f435179ea',
    'resource-instance-multiselect-widget',
    'views/components/widgets/resource-instance-multiselect',
    'resource-instance-list',
    '{
        "placeholder": ""
    }'
);

INSERT INTO d_data_types(
    datatype, iconclass, modulename,
    classname, defaultconfig, configcomponent,
    configname, isgeometric, defaultwidget,
    issearchable
) VALUES (
    'resource-instance-list',
    'fa fa-external-link-square',
    'datatypes.py',
    'ResourceInstanceDataType',
    '{
        "graphid": null
    }',
    'views/components/datatypes/resource-instance',
    'resource-instance-datatype-config',
    FALSE,
    'ff3c400a-76ec-11e7-a793-784f435179ea',
    TRUE
);
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('number', 'fa fa-hashtag', 'datatypes.py', 'NumberDataType', null, null, null, FALSE, '10000000-0000-0000-0000-000000000008');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('date', 'fa fa-calendar', 'datatypes.py', 'DateDataType', null, null, null, FALSE, '10000000-0000-0000-0000-000000000004');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('geojson-feature-collection', 'fa fa-globe', 'datatypes.py', 'GeojsonFeatureCollectionDataType', '{
    "pointColor": "rgba(130, 130, 130, 0.7)",
    "pointHaloColor": "rgba(200, 200, 200, 0.5)",
    "radius": 2,
    "haloRadius": 4,
    "lineColor": "rgba(130, 130, 130, 0.7)",
    "lineHaloColor": "rgba(200, 200, 200, 0.5)",
    "weight": 2,
    "haloWeight": 4,
    "fillColor": "rgba(130, 130, 130, 0.5)",
    "outlineColor": "rgba(200, 200, 200, 0.7)",
    "outlineWeight": 2,
    "layerActivated": true,
    "addToMap": false, "layerIcon": "",
    "layerName": "",
    "clusterDistance": 20,
    "clusterMaxZoom": 5,
    "clusterMinPoints": 3,
    "cacheTiles": false,
    "autoManageCache": false,
    "advancedStyling": false,
    "advancedStyle": ""
}', 'views/graph/datatypes/geojson-feature-collection', 'geojson-feature-collection-datatype-config', TRUE, '10000000-0000-0000-0000-000000000007');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('concept', 'fa fa-list-ul', 'concept_types.py', 'ConceptDataType', '{"rdmCollection": null}', 'views/graph/datatypes/concept', 'concept-datatype-config', FALSE, '10000000-0000-0000-0000-000000000002');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('concept-list', 'fa fa-list-ul', 'concept_types.py', 'ConceptListDataType', '{"rdmCollection": null}', 'views/graph/datatypes/concept', 'concept-datatype-config', FALSE, '10000000-0000-0000-0000-000000000012');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('domain-value', 'fa fa-list-ul', 'concept_types.py', 'ConceptDataType', '{"options": []}', 'views/graph/datatypes/domain-value', 'domain-value-datatype-config', FALSE, '10000000-0000-0000-0000-000000000015');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('domain-value-list', 'fa fa-list-ul', 'concept_types.py', 'ConceptListDataType', '{"options": []}', 'views/graph/datatypes/domain-value', 'domain-value-datatype-config', FALSE, '10000000-0000-0000-0000-000000000016');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('boolean', 'fa fa-toggle-on', 'datatypes.py', 'BooleanDataType', null, null, null, FALSE, '10000000-0000-0000-0000-000000000006');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric, defaultwidget) VALUES ('file-list', 'fa fa-file-image-o', 'datatypes.py', 'FileListDataType', null, null, null, FALSE, '10000000-0000-0000-0000-000000000019');
INSERT INTO d_data_types(datatype, iconclass, modulename, classname, defaultconfig, configcomponent, configname, isgeometric) VALUES ('semantic', 'fa fa-link', 'datatypes.py', 'BaseDataType', null, null, null, FALSE);
INSERT INTO graphs(graphid, name, author, version, description, isresource, iconclass, subtitle, ontologyid, templateid, config)
    VALUES ('22000000-0000-0000-0000-000000000000', '{"en": "Node"}', 'Arches', 'v1', '{"en": "Represents a single node in a graph"}', 'f', 'fa fa-circle', '{"en": "Represents a single node in a graph."}', null, '50000000-0000-0000-0000-000000000001', '{}');

INSERT INTO nodes(nodeid, name, description, istopnode, ontologyclass, datatype, graphid, issearchable, isrequired, hascustomalias)
    VALUES ('20000000-0000-0000-0000-100000000000', 'Node', 'Represents a single node in a graph', 't', 'E1_CRM_Entity', 'semantic', '22000000-0000-0000-0000-000000000000', 't', 'f', 't');

INSERT INTO node_groups(nodegroupid, legacygroupid, cardinality)
    VALUES ('20000000-0000-0000-0000-100000000000', '', 'n');
-- End Node graph

-- Node/NodeType graph
INSERT INTO graphs(graphid, name, author, version, description, isresource, iconclass, subtitle, ontologyid, templateid, config)
    VALUES ('22000000-0000-0000-0000-000000000001', '{"en": "Node/Node Type"}', 'Arches', 'v1', '{"en": "Represents a node and node type pairing"}', 'f', 'fa fa-angle-double-down','{"en": "Represents a node and node type pairing"}', null, '50000000-0000-0000-0000-000000000001', '{}');

INSERT INTO node_groups(nodegroupid, legacygroupid, cardinality)
    VALUES ('20000000-0000-0000-0000-100000000001', '', 'n');

INSERT INTO nodes(nodeid, name, description, istopnode, ontologyclass, datatype,
            graphid, nodegroupid, issearchable, isrequired, hascustomalias)
    VALUES ('20000000-0000-0000-0000-100000000001', 'Node', '', 't', 'E1_CRM_Entity', 'string',
            '22000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-100000000001', 't', 'f', 'f');

INSERT INTO nodes(nodeid, name, description, istopnode, ontologyclass, datatype,
            graphid, nodegroupid, config, issearchable, isrequired, hascustomalias)
    VALUES ('20000000-0000-0000-0000-100000000002', 'Node Type', '', 'f', 'E55_Type', 'concept',
            '22000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-100000000001', '{"rdmCollection": null}', 't', 'f', 'f');


INSERT INTO edges(edgeid, graphid, domainnodeid, rangenodeid, ontologyproperty)
    VALUES ('22200000-0000-0000-0000-000000000001', '22000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-100000000001', '20000000-0000-0000-0000-100000000002', 'P2_has_type');

INSERT INTO card_components(componentid, name, description, component, componentname, defaultconfig)
    VALUES ('4e40b397-d6bc-4660-a398-4a72c90dba07', 'Photo Gallery Card', 'Photo gallery card UI', 'views/components/cards/photo-gallery-card', 'photo-gallery-card', '{}');
INSERT INTO card_components(componentid, name, description, component, componentname, defaultconfig)
    VALUES ('f554c976-9026-463b-a11d-47528e77cf67', 'User Account Card', 'User account related to a person', 'views/components/cards/user_account', 'user-account-card', '{}');
INSERT INTO card_components(componentid, name, description, component, componentname, defaultconfig)
    VALUES ('f05e4d3a-53c1-11e8-b0ea-784f435179ea', 'Name Card', 'Name Card', 'views/components/cards/name', 'name', '{}');
INSERT INTO cards(cardid, name, description, instructions,
        nodegroupid, graphid, active, visible, helpenabled, componentid)
    VALUES ('22200000-0000-0000-0000-900000000001', '{"en": "Node/Node Type"}', '{"en": "Represents a node and node type pairing"}', '{"en": ""}',
        '20000000-0000-0000-0000-100000000001', '22000000-0000-0000-0000-000000000001', 't', 't', 'f', '4e40b397-d6bc-4660-a398-4a72c90dba07');
-- End Node/NodeType graph

INSERT INTO d_value_types VALUES ('scopeNote', 'note', null, 'skos', 'text');
INSERT INTO d_value_types VALUES ('definition', 'note', null, 'skos', 'text');
INSERT INTO d_value_types VALUES ('example', 'note', null, 'skos', 'text');
INSERT INTO d_value_types VALUES ('historyNote', 'note', null, 'skos', 'text');
INSERT INTO d_value_types VALUES ('editorialNote', 'note', null, 'skos', 'text');
INSERT INTO d_value_types VALUES ('changeNote', 'note', null, 'skos', 'text');
INSERT INTO d_value_types VALUES ('note', 'note', null, 'skos', 'text');

--SKOS Lexical Properties
INSERT INTO d_value_types VALUES ('prefLabel', 'label', null, 'skos', 'text');
INSERT INTO d_value_types VALUES ('altLabel', 'label', null, 'skos', 'text');
INSERT INTO d_value_types VALUES ('hiddenLabel', 'label', null, 'skos', 'text');

--SKOS Notation (A notation is different from a lexical label in that a notation is not normally recognizable as a word or sequence of words in any natural language. (ie sortorder))
INSERT INTO d_value_types VALUES ('notation', 'notation', null, 'skos', 'text');

--NON-SKOS
INSERT INTO d_value_types VALUES ('image', 'image', null, 'arches', 'text');

--DUBLIN CORE
INSERT INTO d_value_types VALUES ('title', 'label', null, 'dcterms', 'text');
INSERT INTO d_value_types VALUES ('description', 'note', null, 'dcterms', 'text');
INSERT INTO d_value_types VALUES ('collector', 'undefined', null, 'arches', 'text');

--ARCHES PROPERTIES
INSERT INTO d_value_types VALUES ('sortorder', 'undefined', null, 'arches', 'text');
INSERT INTO d_value_types VALUES ('min_year', 'undefined', null, 'arches', 'text');
INSERT INTO d_value_types VALUES ('max_year', 'undefined', null, 'arches', 'text');
INSERT INTO d_value_types VALUES ('identifier', 'identifiers', null, 'dcterms', 'text');

--SKOS Mapping Properties (relationships between concepts across schemes)
INSERT INTO d_relation_types VALUES ('closeMatch', 'Mapping Properties', 'skos');
INSERT INTO d_relation_types VALUES ('mappingRelation', 'Mapping Properties', 'skos');
INSERT INTO d_relation_types VALUES ('narrowMatch', 'Mapping Properties', 'skos');
INSERT INTO d_relation_types VALUES ('relatedMatch', 'Mapping Properties', 'skos');
INSERT INTO d_relation_types VALUES ('broadMatch', 'Mapping Properties', 'skos');
INSERT INTO d_relation_types VALUES ('exactMatch', 'Mapping Properties', 'skos');

--SKOS Semantic Relations (relationship between concepts within a scheme)
INSERT INTO d_relation_types VALUES ('broader', 'Semantic Relations', 'skos');
INSERT INTO d_relation_types VALUES ('broaderTransitive', 'Semantic Relations', 'skos');
INSERT INTO d_relation_types VALUES ('narrower', 'Semantic Relations', 'skos');
INSERT INTO d_relation_types VALUES ('narrowerTransitive', 'Semantic Relations', 'skos');
INSERT INTO d_relation_types VALUES ('related', 'Semantic Relations', 'skos');
INSERT INTO d_relation_types VALUES ('member', 'Concept Collections', 'skos');
INSERT INTO d_relation_types VALUES ('hasTopConcept', 'Properties', 'skos');

--Arches entityttype relations to concepts
INSERT INTO d_relation_types VALUES ('hasCollection', 'Entitytype Relations', 'arches');

--OWL Class types and Arches specific types
INSERT INTO d_node_types VALUES ('ConceptScheme', 'skos');
INSERT INTO d_node_types VALUES ('Concept', 'skos');
INSERT INTO d_node_types VALUES ('Collection', 'skos');


INSERT INTO concepts(conceptid, nodetype, legacyoid) VALUES ('00000000-0000-0000-0000-000000000001', 'ConceptScheme', 'ARCHES');
INSERT INTO concepts(conceptid, nodetype, legacyoid) VALUES ('00000000-0000-0000-0000-000000000004', 'Concept', 'ARCHES RESOURCE CROSS-REFERENCE RELATIONSHIP TYPES CONCEPT');
INSERT INTO concepts(conceptid, nodetype, legacyoid) VALUES ('00000000-0000-0000-0000-000000000005', 'Collection', 'ARCHES RESOURCE CROSS-REFERENCE RELATIONSHIP TYPES COLLECTION');
INSERT INTO concepts(conceptid, nodetype, legacyoid) VALUES ('00000000-0000-0000-0000-000000000006', 'ConceptScheme', 'CANDIDATES');
INSERT INTO concepts(conceptid, nodetype, legacyoid) VALUES ('00000000-0000-0000-0000-000000000007', 'Concept', 'DEFAULT RESOURCE TO RESOURCE RELATIONSHIP TYPE');


INSERT INTO "values"(valueid, conceptid, valuetype, value, languageid) VALUES ('d8c60bf4-e786-11e6-905a-b756ec83dad5', '00000000-0000-0000-0000-000000000001', 'prefLabel', 'Arches', 'en-US');
INSERT INTO "values"(valueid, conceptid, valuetype, value, languageid) VALUES ('c12e7e6c-e417-11e6-b14b-0738913905b4', '00000000-0000-0000-0000-000000000004', 'prefLabel', 'Resource To Resource Relationship Types', 'en-US');
INSERT INTO "values"(valueid, conceptid, valuetype, value, languageid) VALUES ('d8c622f6-e786-11e6-905a-475a5eee86f5', '00000000-0000-0000-0000-000000000005', 'prefLabel', 'Resource To Resource Relationship Types', 'en-US');
INSERT INTO "values"(valueid, conceptid, valuetype, value, languageid) VALUES ('fee39428-e83f-11e6-b49d-9b976819ac02', '00000000-0000-0000-0000-000000000006', 'prefLabel', 'Candidates', 'en-US');
INSERT INTO "values"(valueid, conceptid, valuetype, value, languageid) VALUES ('ac41d9be-79db-4256-b368-2f4559cfbe55', '00000000-0000-0000-0000-000000000007', 'prefLabel', 'is related to', 'en-US');


INSERT INTO relations(relationid, conceptidfrom, conceptidto, relationtype)
    VALUES ('0158f687-c0c5-4675-817f-9682a613bb13', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', 'hasTopConcept');

INSERT INTO relations(relationid, conceptidfrom, conceptidto, relationtype)
    VALUES ('f552511a-26a1-4e70-ae01-b511bb022460', '00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000007', 'member');

INSERT INTO functions(functionid, modulename, classname, functiontype, name, description, defaultconfig, component)
    VALUES ('60000000-0000-0000-0000-000000000000', 'local_file_storage.py', 'LocalFileStorageFunction', 'node', 'Local File Upload', 'Sets the default storage mechanism for uploaded files', '{}', 'views/components/functions/local-file-storage');

INSERT INTO functions(functionid, modulename, classname, functiontype, name, description, defaultconfig, component)
    VALUES ('60000000-0000-0000-0000-000000000001', 'primary_descriptors.py', 'PrimaryDescriptorsFunction', 'primarydescriptors', 'Define Resource Descriptors', 'Configure the name, description, and map popup of a resource', '{"module": "arches.app.functions.primary_descriptors", "class_name":"PrimaryDescriptorsFunction", "descriptor_types": {"name": {"nodegroup_id": "", "string_template": ""}, "description": {"nodegroup_id": "", "string_template":""}, "map_popup": {"nodegroup_id": "", "string_template":""}} }', 'views/components/functions/primary-descriptors');

INSERT INTO functions(functionid, modulename, classname, functiontype, name, description, defaultconfig, component)
    VALUES ('60000000-0000-0000-0000-000000000002', 'required_nodes.py', 'RequiredNodesFunction', 'validation', 'Define Required Nodes', 'Define which values are required for a user to save card', '{"required_nodes":"{}"}', 'views/components/functions/required-nodes');
INSERT INTO auth_user(username, password, is_superuser, first_name, last_name, email, is_staff, is_active, date_joined) VALUES ('anonymous', '', false, 'Anonymous', 'User', '', false, true, datetime());

INSERT INTO etl_modules (
    etlmoduleid,
    name,
    description,
    etl_type,
    component,
    componentname,
    modulename,
    classname,
    config,
    icon,
    slug,
    reversible)
VALUES (
    'a6af3a25-50ac-47a1-a876-bcb13dab411b',
    'Bulk import via Well-Known Resource Model',
    'Import from WKRM',
    'import',
    'bulk-import-wkrm',
    'bulk-import-wkrm',
    '_bulk_import_wkrm.py',
    'BulkImportWKRM',
    '{"bgColor": "#0591ef", "circleColor": "#00adf3", "show": false}',
    'fa fa-upload',
    'bulk-import-wkrm',
    true);
