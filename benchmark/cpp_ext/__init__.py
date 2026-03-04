"""C++ extension modules for Python benchmark using pybind11."""

try:
    from . import numeric
    from . import memory
    from . import parallel
except ImportError as e:
    import warnings
    warnings.warn(f"Failed to import C++ extensions: {e}. "
                  "Make sure to build the extensions first using: "
                  "cd benchmark/cpp_ext && python setup.py build_ext --inplace")
    numeric = None
    memory = None
    parallel = None

__all__ = ['numeric', 'memory', 'parallel']
