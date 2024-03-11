from babelfont.convertors.glyphs.glyphs3 import GlyphsThree
import os
import openstep_plist
import glob


class GlyphsPackage(GlyphsThree):
    suffix = ".glyphspackage"

    @classmethod
    def can_save(cls, convertor, **kwargs):
        return False

    @classmethod
    def can_load(cls, other, **kwargs):
        return other.filename.endswith(cls.suffix)

    def _load(self):
        infofile = os.path.join(self.filename, "fontinfo.plist")
        # orderfile = os.path.join(self.filename, "order.plist")
        # glyphorder = openstep_plist.load(open(orderfile, "r"))
        self.scratch["plist"] = openstep_plist.load(
            open(infofile, "r"), use_numbers=True
        )
        self.scratch["plist"]["glyphs"] = []
        for glyphfile in glob.glob(os.path.join(self.filename, "glyphs", "*")):
            self.scratch["plist"]["glyphs"].append(
                openstep_plist.load(open(glyphfile, "r"), use_numbers=True)
            )

        return super()._load()
