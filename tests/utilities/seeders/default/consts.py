PERSON_DATATYPE_NODE_ALIAS_KEYS = {
    'domain-value': [
            'family_members', 
                'family_members_amount'
        ],
    'string': [
        'family_members',
            'pet'
    ],
    'number': [
        'system_reference_numbers', 
            'primaryreferencenumber',
                'primary_reference_number'
    ],
    'date': [
        'audit_metadata', 
            'audit_creation',
                'creation_timespan',
                    'creation_end_date'
    ]
}

ACTIVITY_DATATYPE_NODE_ALIAS_KEYS = {
    'concept': [
        'record_status_assignment',
            'record_status'
    ]
}