from collections import OrderedDict, defaultdict
import datetime
import math
import re
import uuid
import logging
from pathlib import Path

from babelfont.BaseObject import OTValue
from babelfont.convertors import BaseConvertor

from babelfont import (
    Anchor,
    Axis,
    Master,
    Instance,
    Guide,
    Glyph,
    Layer,
    Node,
    Shape,
    Transform,
)

NUMBER = r"(-?\d+(?:\.\d+)?(?:e-?\d+)?)"
MOVE_RE = re.compile(rf"^\s*{NUMBER}\s+{NUMBER}\s+m")
CURVE_RE = re.compile(
    rf"^\s*{NUMBER}\s+{NUMBER}\s+{NUMBER}\s+{NUMBER}\s+{NUMBER}\s+{NUMBER} c"
)
LINE_RE = re.compile(rf"^\s*{NUMBER}\s+{NUMBER}\s+l")

log = logging.getLogger(__name__)


class FontForgeSFDIR(BaseConvertor):
    suffix = ".sfdir"
    IGNORE = [
        "SplineFontDB",
        "UComments",
        "TeXData",
        "FontName",
        "DefaultBaseFilename",
        "sfntRevision",
        "InvalidEm",
        "XUID",
        "OS2Version",
        "PfmFamily",
        "AntiAlias",
        "FitToEm",
        "DisplaySize",
        "Validated",
        "Flags",
        "VWidth",
        "Lookup",
        "Substitution2",  # Urgh
    ]

    @classmethod
    def can_save(cls, convertor, **kwargs):
        return False

    def _load(self):
        font = self.font
        self.current_glyph = None
        # I'm going to assume a single master font
        font.masters = [Master(name="Regular", id=str(uuid.uuid4()), font=font)]

        self.info = open(Path(self.filename) / "font.props").read().splitlines()
        self._load_line("info")
        # Probe once for glyphorder
        self.glyph_order = {}
        for fontfile in Path(self.filename).glob("*.glyph"):
            self._probe_glyphorder(fontfile)
        for gid in sorted(self.glyph_order.keys()):
            self.font.glyphs.append(Glyph(name=self.glyph_order[gid]))

        for fontfile in Path(self.filename).glob("*.glyph"):
            self.info = open(fontfile).read().splitlines()
            self._load_line("glyph")

        return font

    def _probe_glyphorder(self, file):
        glyphname = ""
        for line in open(file).readlines():
            if m := re.match(r"StartChar: (.*)", line):
                glyphname = m.group(1)
                continue
            if m := re.match(r"Encoding: (\d+) (-?\d+) (\d+)", line):
                gid = int(m.group(3))
                if not glyphname:
                    raise ValueError(f"Bad file {file} - no StartChar")
                self.glyph_order[gid] = glyphname
                break

    def _load_line(self, mode):
        while self.info:
            line = self.info.pop(0)
            if line == "EndSplineFont" and mode == "info":
                break
            if line == "EndChar" and mode == "glyph":
                break
            if ": " not in line:
                if hasattr(self, "_handle_" + line):
                    getattr(self, "_handle_" + line)()
                    continue
                else:
                    raise ValueError("Bad font.props file - " + line)
            key, value = line.split(": ", 1)
            if key in self.IGNORE:
                continue
            if hasattr(self, "_handle_" + key):
                getattr(self, "_handle_" + key)(value)
            # else:
            #     log.warn("Unknown info key %s", key)

    def _handle_FamilyName(self, value):
        self.font.names.familyName.set_default(value)

    def _handle_FullName(self, value):
        self.font.names.compatibleFullName.set_default(value)

    def _handle_Copyright(self, value):
        self.font.names.copyright.set_default(value)

    def _handle_Comments(self, value):
        self.font.notes = value

    def _handle_Version(self, value):
        self.font.names.version.set_default(value)
        self.font.version = [int(x) for x in value.split(".")]

    def _handle_Weight(self, value):
        self.font.names.typographicSubfamily.set_default(value)

    def _handle_Fontlog(self, value):
        self.font.names.description.set_default(value)

    def _handle_ItalicAngle(self, value):
        self.font.customOpenTypeValues.append(
            OTValue("post", "italicAngle", float(value))
        )

    def _handle_UnderlinePosition(self, value):
        self.font.customOpenTypeValues.append(
            OTValue("post", "underlinePosition", int(value))
        )

    def _handle_UnderlineWidth(self, value):
        self.font.customOpenTypeValues.append(
            OTValue("post", "underlineThickness", int(value))
        )

    def _handle_Ascent(self, value):
        self.font.masters[0].metrics["ascender"] = int(value)

    def _handle_Descent(self, value):
        self.font.masters[0].metrics["descender"] = -int(value)

    def _handle_LayerCount(self, value):
        # Ignore layers for now
        pass

    def _handle_Layer(self, value):
        # Ignore layers for now
        pass

    def _handle_FSType(self, value):
        self.font.customOpenTypeValues.append(OTValue("OS/2", "fsType", int(value)))

    def _handle_OS2_WeightWidthSlopeOnly(self, value):
        # XXX
        self.font.customOpenTypeValues.append(
            OTValue("OS/2", "fsSelection", int(value))
        )

    def _handle_OS2_UseTypoMetrics(self, value):
        if not value:
            return
        for otval in self.font.customOpenTypeValues:
            if otval.table == "OS/2" and otval.field == "fsSelection":
                otval.value = otval.value | 7 << 1
                return
        self.font.customOpenTypeValues.append(OTValue("OS/2", "fsSelection", 7))

    def _handle_CreationTime(self, value):
        self.font.customOpenTypeValues.append(
            OTValue("head", "created", datetime.datetime.fromtimestamp(int(value)))
        )

    def _handle_ModificationTime(self, value):
        self.font.customOpenTypeValues.append(
            OTValue("head", "modified", datetime.datetime.fromtimestamp(int(value)))
        )

    def _handle_ShortTable(self, value):
        # Ignore short table for now
        while self.info:
            line = self.info.pop(0)
            if line.startswith("EndShort"):
                break

    def _handle_TtTable(self, value):
        while self.info:
            line = self.info.pop(0)
            if line.startswith("EndTTInstrs"):
                break

    def _handle_BeginPrivate(self, value):
        while self.info:
            line = self.info.pop(0)
            if line.startswith("EndPrivate"):
                break

    def _handle_Grid(self):
        grid = Layer(name="grid", id="grid", _master="default", _font=self.font)
        self._expect_splineset(grid.getPen())

    def _handle_StartChar(self, value):
        self.current_glyph = self.font.glyphs[value]
        self.current_glyph.layers = [
            Layer(
                name="default",
                id=self.font.masters[0].id,
                _master=self.font.masters[0].id,
                _font=self.font,
            )
        ]

    def _handle_Encoding(self, value):
        if not self.current_glyph:
            return
        _old, unicode, gid = value.split()
        if unicode != "-1":
            self.current_glyph.codepoints.append(int(unicode))

    def _handle_Width(self, value):
        self.current_glyph.layers[0].width = int(value)

    def _handle_GlyphClass(self, value):
        pass

    def _handle_Fore(self):
        self._expect_splineset(self.current_glyph.layers[0].getPen())

    def _handle_Refer(self, value: str):
        gid, unicode, style, xx, xy, yx, yy, dx, dy, ttflag = value.split(None, 10)
        component = Shape(
            ref=self.glyph_order[int(gid)],
            transform=Transform(
                float(xx), float(xy), float(yx), float(yy), float(dx), float(dy)
            ),
        )
        self.current_glyph.layers[0].shapes.append(component)

    def _expect_splineset(self, pen):
        paths = False
        while self.info:
            line = self.info.pop(0)
            if line == "SplineSet":
                continue
            if line.startswith("EndSplineSet"):
                break
            if m := re.match(MOVE_RE, line):
                if paths:
                    pen.closePath()
                pen.moveTo((float(m.group(1)), float(m.group(2))))
            elif m := re.match(CURVE_RE, line):
                if (float(m.group(1)), float(m.group(2))) == (
                    float(m.group(3)),
                    float(m.group(4)),
                ):
                    # Quadratic in disguise
                    pen.qCurveTo(
                        (float(m.group(1)), float(m.group(2))),
                        (float(m.group(5)), float(m.group(6))),
                    )
                else:
                    pen.curveTo(
                        (float(m.group(1)), float(m.group(2))),
                        (float(m.group(3)), float(m.group(4))),
                        (float(m.group(5)), float(m.group(6))),
                    )
                paths = True
            elif m := re.match(LINE_RE, line):
                pen.lineTo((float(m.group(1)), float(m.group(2))))
                paths = True
            else:
                # Put back
                self.info.insert(0, line)
                break
        if paths:
            pen.closePath()
        return
