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


def format_file_size(size_bytes: int) -> str:
    """Format byte count to human-readable string (e.g. '6.27 GB')."""
    if size_bytes < 1024:
        return f'{size_bytes} B'
    if size_bytes < 1024 ** 2:
        return f'{size_bytes / 1024:.2f} KB'
    if size_bytes < 1024 ** 3:
        return f'{size_bytes / (1024 ** 2):.2f} MB'
    if size_bytes < 1024 ** 4:
        return f'{size_bytes / (1024 ** 3):.2f} GB'
    return f'{size_bytes / (1024 ** 4):.2f} TB'


def parse_size_to_bytes(size_str: str) -> int:
    """Parse '6.27 GB' style string to integer bytes. Returns 0 on failure."""
    try:
        parts = size_str.strip().split()
        if len(parts) == 2:
            val = float(parts[0])
            unit = parts[1].upper()
            multipliers = {'TB': 1024**4, 'GB': 1024**3, 'MB': 1024**2, 'KB': 1024}
            return int(val * multipliers.get(unit, 1))
    except (ValueError, IndexError):
        pass
    return 0
