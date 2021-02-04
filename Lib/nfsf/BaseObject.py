from dataclasses import dataclass
from ruamel.yaml import YAML
from io import StringIO
from collections import namedtuple
import datetime


Color = namedtuple("Color", "r,g,b,a", defaults=[0,0,0,0])
Position = namedtuple("Position", "x,y,angle", defaults=[0,0,0])
_Node = namedtuple("Node", "x,y,type,userdata", defaults=[0,0,"c",None])

@dataclass
class BaseObject:
    _serialize_slots = []
    _write_one_line = False
    _separate_items = {}

    def __post_init__(self):
        self._formatspecific = {}

    def _write_value(self, stream, k, v, indent=0):
        if hasattr(v, "write"):
            v.write(stream, indent+1)
        elif isinstance(v, tuple):
            stream.write(b"[")
            for ix,l in enumerate(v):
                self._write_value(stream, k, l, indent+1)
                if ix < len(v)-1:
                    stream.write(b", ")
            stream.write(b"]")
        elif isinstance(v, dict):
            stream.write(b"{")
            for ix,(k1,v1) in enumerate(v.items()):
                self._write_value(stream, k, k1, indent+1)
                stream.write(b": ")
                self._write_value(stream, k, v1, indent+1)
                if ix < len(v.items())-1:
                    stream.write(b", ")
            stream.write(b"}")
        elif isinstance(v, list):
            stream.write(b"[")
            for ix,l in enumerate(v):
                if k in self._separate_items:
                    stream.write(b"\n")
                    stream.write(b"  " * (indent+2))
                self._write_value(stream, k, l, indent+1)
                if ix < len(v)-1:
                    stream.write(b", ")
            if k in self._separate_items:
                stream.write(b"\n")
                stream.write(b"  " * (indent+1))
            stream.write(b"]")
        elif isinstance(v, datetime.datetime):
            stream.write('"{0}"'.format(v.__str__()).encode())
        elif isinstance(v, str):
            stream.write('"{0}"'.format(v).encode())
        else:
            stream.write(str(v).encode())

    def write(self, stream, indent = 0):
        if not self._write_one_line:
            stream.write(b"  " * indent)
        stream.write(b"{")
        towrite = []
        for k in self._serialize_slots:
            v = getattr(self, k)
            default = None

            if k in self.__dataclass_fields__:
                default = self.__dataclass_fields__[k].default
            if not v or (default and v == default):
                continue
            towrite.append((k,v))

        for ix, (k,v) in enumerate(towrite):
            if not self._write_one_line:
                stream.write(b"\n")
                stream.write(b"  " * (indent+1))

            stream.write('"{0}": '.format(k).encode())
            self._write_value(stream, k, v, indent)
            if ix != len(towrite) -1:
                stream.write(b", ")

        stream.write(b"}")
        if not self._write_one_line:
            stream.write(b"\n")


class Node(_Node):
    def write(self, stream, indent):
        if not self.userdata:
            stream.write( ('[%i,%i,"%s"]' % (self.x, self.y, self.type)).encode())
        else:
            stream.write( ('[%i,%i,"%s", "%s"]' % (self.x, self.y, self.type, self.userdata)).encode())
