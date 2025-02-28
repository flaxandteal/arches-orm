from typing import Dict, List;

PERSON_DEFAULT_SEED_PATH = 'default/person'
ACTIVITY_DEFAULT_SEED_PATH = 'default/activity'

PERSON_DATATYPE_NODE_ALIAS_KEYS: Dict[str, List[str]] = {
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
    ],
    'boolean': [
        'family_members',
            'cars'
    ]
}

ACTIVITY_DATATYPE_NODE_ALIAS_KEYS: Dict[str, List[str]] = {
    'concept': [
        'record_status_assignment',
            'record_status'
    ]
}