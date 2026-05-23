"""Shared tag manipulation utilities."""


def merge_tags(existing_str, add_tags=None, remove_tags=None):
    """Merge tags: existing comma-separated string + add list - remove list."""
    current = set(t.strip() for t in existing_str.split(',') if t.strip())
    if add_tags:
        current.update(t.strip() for t in add_tags if t.strip())
    if remove_tags:
        current.difference_update(t.strip() for t in remove_tags if t.strip())
    return ','.join(sorted(current))
