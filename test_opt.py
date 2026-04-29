def _map_task_to_domain(description: str):
    DOMAIN_KEYWORD_MAPPING = {
        'CHEMISTRY': ['chemistry', 'chemical', 'molecule', 'compound'],
        'BIOLOGY': ['biology', 'biological', 'organism', 'cell', 'dna'],
    }
    description = description.lower()
    for domain, keywords in DOMAIN_KEYWORD_MAPPING.items():
        for keyword in keywords:
            if keyword in description:
                return domain
    return None

print(_map_task_to_domain("this is a chemical test"))
