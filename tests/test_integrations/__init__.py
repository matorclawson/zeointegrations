"""Provider cases run through the full gate's explicit pytest invocation."""


def load_tests(loader, tests, pattern):
    """Keep dependency-free unittest discovery separate from provider pytest."""
    del loader, pattern
    return tests
