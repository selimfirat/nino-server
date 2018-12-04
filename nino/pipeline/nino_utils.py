import importlib
path = 'nino_modules'

class_references = {}
def request_class_references(module_names):
    crs = [getattr(importlib.import_module('.'+name, path), name) for name in module_names]
    return dict(zip(module_names, crs))

def request_default_objects(module_names):
    return [getattr(importlib.import_module('.'+name, path), name)() for name in module_names]

def load_modules():
    crs = [getattr(importlib.import_module('.'+name, path), name) for name in module_names]
    global class_references
    class_references = dict(zip(module_names, crs))

def get_class_references():
    global class_references
    return class_references

module_names = [
  "PreprocessModule",
  "RegionSegmentationModule"
]
