"""Compatibility import for legacy scripts and tests.

The production implementation lives in ``blank_business_builder`` so it is
installed with BBB images and available to Echo Prime in Kubernetes.
"""

from blank_business_builder.bbb_unified_business_library import *  # noqa: F401,F403
