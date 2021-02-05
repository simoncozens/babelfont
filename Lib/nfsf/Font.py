from .BaseObject import BaseObject
from .Glyph import GlyphList
from pathlib import Path
from fontTools.misc.filenames import userNameToFileName
from .Names import Names


class Font(BaseObject):
    _serialize_slots = [
        "upm",
        "version",
        "axes",
        "instances",
        "masters",
        "note",
        "date",
    ]
    _separate_items = { "instances": True, "axes": True, "glyphs": True, "masters": True }

    def __init__(self):
        super().__init__()
        self.axes = []
        self.masters = []
        self.glyphs = GlyphList()
        self.instances = []
        self.names = Names()
        self._formatspecific = {}
        self.date = None

    def save(self, pathname):
        path = Path(pathname)
        path.mkdir(parents=True, exist_ok=True)

        with open(path / "info.json", "wb") as f:
            self.write(stream=f)

        with open(path / "names.json", "wb") as f:
            self._write_value(f, "glyphs", self.names)

        with open(path / "glyphs.json", "wb") as f:
            for g in self.glyphs:
                glyphpath = path / "glyphs"
                glyphpath.mkdir(parents=True, exist_ok=True)
                with open(glyphpath / (userNameToFileName(g.name)+".nfsglyph"), "wb") as f2:
                    g._write_value(f2, "layers", g.layers)
            self._write_value(f, "glyphs", self.glyphs)
