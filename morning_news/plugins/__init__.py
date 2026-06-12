"""Plugin module for Morning News - auto-discovers and loads info source plugins."""

import importlib
import pkgutil
from typing import Dict, Type
from morning_news.plugins.base import BasePlugin


def discover_plugins() -> Dict[str, Type[BasePlugin]]:
    """Discover all plugin classes in the plugins package.

    Scans morning_news.plugins for modules containing classes that inherit from BasePlugin.
    Returns a dict mapping plugin name to plugin class.

    Returns:
        Dict of {plugin_name: plugin_class} for all discovered plugins.
    """
    plugins = {}
    package_dir = __path__[0]

    for module_info in pkgutil.iter_modules([package_dir]):
        # Skip base module and template
        if module_info.name in ("base", "template"):
            continue

        try:
            module = importlib.import_module(f"morning_news.plugins.{module_info.name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                    and attr.name  # Must have a non-empty name
                ):
                    plugins[attr.name] = attr
        except ImportError:
            continue

    return plugins