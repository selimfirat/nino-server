import importlib
path = 'nino_modules'
def request_class_references(module_names):
    crs = [getattr(importlib.import_module('.'+name, path), name) for name in module_names]
    return dict(zip(module_names, crs))

def request_default_objects(module_names):
    return [getattr(importlib.import_module('.'+name, path), name)() for name in module_names]
