from dataclasses import dataclass

TO_PEN_TYPE = {"o": None, "c": "curve", "l": "line", "q": "qcurve"}
FROM_PEN_TYPE = {v: k for k, v in TO_PEN_TYPE.items()}


@dataclass
class Node:
    x: int = 0
    y: int = 0
    type: str = "c"
    userdata: str = None

    def write(self, stream, _indent):
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
        return TO_PEN_TYPE[self.type[0]]
