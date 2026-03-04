"""Pure Python implementation module."""

from .numeric import find_primes, matrix_multiply
from .memory import sort_array, filter_array
from .parallel import parallel_compute

__all__ = [
    'find_primes',
    'matrix_multiply',
    'sort_array',
    'filter_array',
    'parallel_compute',
]
