"""Pytest configuration for benchmark tests."""

from hypothesis import settings, Verbosity

# Configure Hypothesis to run at least 100 iterations per property test
settings.register_profile(
    "benchmark",
    max_examples=100,
    verbosity=Verbosity.normal,
    deadline=None,  # No deadline for performance tests
)

settings.load_profile("benchmark")
