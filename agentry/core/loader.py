import importlib
import pkgutil


def _import_package(package_name):
    package = importlib.import_module(package_name)
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
        full = f"{package_name}.{name}"
        importlib.import_module(full)
        if is_pkg:
            _import_package(full)


def load_plugins():
    _import_package("agentry.providers")
    _import_package("agentry.steps")
    _import_package("agentry.tools")
