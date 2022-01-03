import re

def snake_case(name: str):
    """
    https://stackoverflow.com/a/1176023/1371716
    """
    name = re.sub('(\\.)', r'_', name)
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('__([A-Z])', r'_\1', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.lower()

def capfirst(value: str):
    return value[:1].upper() + value[1:]

def simple_singular(value: str):
    if value.endswith('ies'):
        return value[:-3] + 'y'
    elif value.endswith('s'):
        return value[:-1]
    else:
        return value
        