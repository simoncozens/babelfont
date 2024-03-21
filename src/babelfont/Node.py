from dataclasses import dataclass


@dataclass
class Node:
    x: int = 0
    y: int = 0
    type: str = "c"
    userdata: str = None

    _to_pen_type = {"o": None, "c": "curve", "l": "line", "q": "qcurve"}
    _from_pen_type = {v: k for k, v in _to_pen_type.items()}

    def write(self, stream, indent):
        if not self.userdata:
            stream.write(('[%i,%i,"%s"]' % (self.x, self.y, self.type)).encode())
        else:
            stream.write(
                (
                    '[%i,%i,"%s", "%s"]' % (self.x, self.y, self.type, self.userdata)
                ).encode()
            )

    @property
    def is_smooth(self):
        return self.type.endswith("s")

    @property
    def pen_type(self):
        return self._to_pen_type[self.type[0]]
