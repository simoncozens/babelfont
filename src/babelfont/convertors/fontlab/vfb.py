import datetime
import re
import math

from vfbLib.vfb.vfb import Vfb
from fontTools.misc.transform import Transform

from babelfont import Axis, Glyph, Layer, Master, Node, Shape, Guide
from babelfont.BaseObject import Color, I18NDictionary, OTValue
from babelfont.convertors import BaseConvertor

ignore = [
    "Encoding Mac",
    "Encoding",
    "Master Count",
    "Default Weight Vector",
    "Type 1 Unique ID",
    "Menu Name",
    "FOND Name",
    "weight_name",  # Do something with this?
    "width_name",  # Do something with this?
    "weight",  # Do something if single master
    "trademark",
    "Monospaced",
    "Slant Angle",
    "Background Bitmap",
    "Glyph Origin",
    "Glyph Anchors Supplemental",
    "Links",
]
names = {
    "description": "description",
    "License": "license",
    "License URL": "licenseURL",
    "designer": "designer",
    "designerURL": "designerURL",
    "manufacturer": "manufacturer",
    "manufacturerURL": "manufacturerURL",
    "copyright": "copyright",
    "sgn": "familyName",
    "tfn": "familyName",
    "versionFull": "version",
}


class FontlabVFB(BaseConvertor):
    suffix = ".vfb"

    def _load(self):
        self.vfb = Vfb(self.filename)
        self.vfb.decompile()
        self.current_glyph = None
        for e in self.vfb.entries:
            name = e.key
            if name is None:
                raise TypeError
            data = e.decompiled
            if data is None:
                continue

            if name in ignore or re.match("^\d+$", name):
                continue

            if name == "psn":
                # Postscript name, hey we don't have that.
                pass
            elif name in names:
                if data:
                    setattr(
                        self.font.names, names[name], I18NDictionary.with_default(data)
                    )
            elif name == "ffn":  # Full family name?
                pass
            elif name == "upm":
                self.font.upm = int(data)
            elif name == "versionMajor":
                self.font.version = (int(data), self.font.version[1])
            elif name == "versionMinor":
                self.font.version = (self.font.version[0], int(data))
            elif name == "vendorID":
                self.font.customOpenTypeValues.append(
                    OTValue("OS/2", "achVendID", data)
                )
            elif name == "Glyph":
                self.current_glyph = Glyph(name=data["name"])
                self.font.glyphs.append(self.current_glyph)
            elif name == "Glyph Unicode":
                self.current_glyph.codepoints = data
            elif name == "Italic Angle":
                # Put in master
                pass
            else:
                print(name, data)

        return self.font
