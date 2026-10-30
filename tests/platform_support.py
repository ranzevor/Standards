"""Native test fixtures that require Windows symbolic-link privileges."""
from pathlib import Path
import unittest


def make_symlink(link, target, *, target_is_directory=False):
    try:
        Path(link).symlink_to(target, target_is_directory=target_is_directory)
    except OSError as error:
        if getattr(error, 'winerror', None) != 1314:
            raise
        raise unittest.SkipTest('Windows symbolic-link privilege is unavailable') from error
