"""
config package
==============
Exports the configuration registry so that the application factory
can resolve a config class by name string.
"""

from .settings import (  # noqa: F401
    BaseConfig,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    config_registry,
)
