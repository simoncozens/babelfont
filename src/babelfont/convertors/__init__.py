import os
import sys
import pkgutil
import inspect
import importlib

from babelfont import Font

class BaseConvertor:
    filename: str
    scratch: object
    font: Font
    compile_only: bool

    suffix = ".XXX"

    @classmethod
    def can_load(cls, other, **kwargs):
        return other.filename.endswith(cls.suffix)

    @classmethod
    def can_save(cls, other, **kwargs):
        return other.filename.endswith(cls.suffix)

    @classmethod
    def load(cls, convertor, compile_only=False):
        self = cls()
        self.font = Font()
        # Pass on information to child
        self.filename = convertor.filename
        self.scratch = convertor.scratch
        self.compile_only = compile_only

        return self._load()

    @classmethod
    def save(cls, obj, convertor, **kwargs):
        self = cls()
        self.font = obj
        # Pass on information to child
        self.filename = convertor.filename
        self.scratch = convertor.scratch
        return self._save()

    def _load(self):
        raise NotImplementedError

    def _save(self):
        raise NotImplementedError

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
            spec = loader.find_spec(module_name)
            _module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_module)
            classes = [
                x[1]
                for x in inspect.getmembers(_module, inspect.isclass)
                if issubclass(x[1], BaseConvertor) and x[1] is not BaseConvertor
            ]
            cls.convertors.extend(classes)

    def __init__(self, filename):
        self._load_convertors()
        self.filename = filename
        self.scratch = {}

    def load(self, **kwargs):
        for c in self.convertors:
            if c.can_load(self, **kwargs):
                return c.load(self, **kwargs)
        raise NotImplementedError

    def save(self, obj, **kwargs):
        for c in self.convertors:
            if c.can_save(self, **kwargs):
                return c.save(obj, self, **kwargs)
        raise NotImplementedError
