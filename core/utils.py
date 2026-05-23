"""Shared utility functions used across core modules."""

import os


def resolve_conflict(path):
    """If path exists, append _1, _2, etc. until we find a free name."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    index = 1
    while os.path.exists(path):
        path = f'{base}_{index}{ext}'
        index += 1
    return path
