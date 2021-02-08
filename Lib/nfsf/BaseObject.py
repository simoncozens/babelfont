from dataclasses import dataclass, fields
import orjson
from io import StringIO
from collections import namedtuple
import datetime


Color = namedtuple("Color", "r,g,b,a", defaults=[0, 0, 0, 0])
Position = namedtuple("Position", "x,y,angle", defaults=[0, 0, 0])


class I18NDictionary(dict):
    def copy_in(self, other):
        for k, v in other.items():
            self[k] = v

    def get_default(self):
        if "dflt" in self:
            return self["dflt"]
        else:
            return list(self.values())[0]

    def set_default(self, value):
        if value:
            self["dflt"] = value

    def write(self, stream, indent):
        if len(self.keys()) > 1:
            stream.write(orjson.dumps(self))
        else:
            stream.write('"{0}"'.format(self.get_default()).encode())


@dataclass
class BaseObject:
    _write_one_line = False
    _separate_items = {}

    def __post_init__(self):
        self._formatspecific = {}

    def _should_separate_when_serializing(self, key):
        if key in self.__dataclass_fields__ and "separate_items" in self.__dataclass_fields__[key].metadata:
             return True
        return False

    def _write_value(self, stream, k, v, indent=0):
        if hasattr(v, "write"):
            v.write(stream, indent + 1)
        elif isinstance(v, tuple):
            stream.write(b"[")
            for ix, l in enumerate(v):
                self._write_value(stream, k, l, indent + 1)
                if ix < len(v) - 1:
                    stream.write(b", ")
            stream.write(b"]")
        elif isinstance(v, dict):
            stream.write(b"{")
            for ix, (k1, v1) in enumerate(v.items()):
                self._write_value(stream, k, k1, indent + 1)
                stream.write(b": ")
                self._write_value(stream, k, v1, indent + 1)
                if ix < len(v.items()) - 1:
                    stream.write(b", ")
            stream.write(b"}")
        elif isinstance(v, list):
            stream.write(b"[")
            for ix, l in enumerate(v):
                if self._should_separate_when_serializing(k):
                    stream.write(b"\n")
                    stream.write(b"  " * (indent + 2))
                self._write_value(stream, k, l, indent + 1)
                if ix < len(v) - 1:
                    stream.write(b", ")
            if self._should_separate_when_serializing(k):
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))
            stream.write(b"]")
        elif isinstance(v, datetime.datetime):
            stream.write('"{0}"'.format(v.__str__()).encode())
        elif isinstance(v, str):
            stream.write('"{0}"'.format(v).encode())
        else:
            stream.write(str(v).encode())

    def write(self, stream, indent=0):
        if not self._write_one_line:
            stream.write(b"  " * indent)
        stream.write(b"{")
        towrite = []
        for f in fields(self):
            k = f.name
            if "skip_serialize" in f.metadata:
                continue
            v = getattr(self, k)
            default = f.default
            if not v or (default and v == default):
                continue
            towrite.append((k, v))

        for ix, (k, v) in enumerate(towrite):
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))

            stream.write('"{0}": '.format(k).encode())
            self._write_value(stream, k, v, indent)
            if ix != len(towrite) - 1:
                stream.write(b", ")

        if hasattr(self, "_formatspecific") and self._formatspecific:
            stream.write(b",")
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent + 1))
            stream.write(b'"_":')
            if self._write_one_line:
                stream.write(orjson.dumps(self._formatspecific))
            else:
                stream.write(b"\n")
                stream.write(
                    orjson.dumps(self._formatspecific, option=orjson.OPT_INDENT_2)
                )

        if not self._write_one_line:
            stream.write(b"\n")
        stream.write(b"}")
        if not self._write_one_line:
            stream.write(b"\n")
