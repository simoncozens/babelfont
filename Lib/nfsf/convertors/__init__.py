import os
import sys
import pkgutil
import inspect


class BaseConvertor:
    suffix = ".XXX"

    @classmethod
    def can_load(self, other):
        return other.filename.endswith(self.suffix)

    def can_save(self, other):
        return other.filename.endswith(self.suffix)


class Convert:
    convertors = []

    @classmethod
    def _load_convertors(cls):
        if cls.convertors:
            return
        convertorpath = os.path.join(
            os.path.dirname(sys.modules[cls.__module__].__file__)
        )
        # Additional plugin path here?
        loaders = pkgutil.iter_modules([convertorpath])
        for loader, module_name, is_pkg in loaders:
            if is_pkg:
                continue
            _module = loader.find_module(module_name).load_module(module_name)
            classes = [
                x[1]
                for x in inspect.getmembers(_module, inspect.isclass)
                if issubclass(x[1], BaseConvertor)
            ]
            cls.convertors.extend(classes)

    def __init__(self, filename):
        self._load_convertors()
        self.filename = filename
        self.scratch = {}

    def load(self, **kwargs):
        for c in self.convertors:
            if c.can_load(self):
                return c.load(self, **kwargs)
        raise NotImplementedError

    def save(self, obj):
        for c in self.convertors:
            if c.can_save(self):
                return c.save(obj, self)
        raise NotImplementedError
