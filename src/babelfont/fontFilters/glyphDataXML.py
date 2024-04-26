import logging
from importlib.resources import files
from xml.etree import ElementTree

from babelfont import Font

logger = logging.getLogger(__name__)


def bake_in_glyphdata(font: Font, args=None):
    logger.info("Baking in glyph data")

    if not args or "file" not in args:
        data_dir = files("babelfont.data")
        file = data_dir / "GlyphData.xml"
    else:
        file = args["file"]

    parsed = ElementTree.parse(open(file, "rb")).getroot()
    for glyph in parsed:
        data = glyph.attrib
        if data["name"] not in font.glyphs:
            continue
        myglyph = font.glyphs[data["name"]]
        if "production" in data and not myglyph.production_name:
            myglyph.production_name = data["production"]
        if "category" in data and not myglyph.category:
            if data["category"] == "Mark":
                myglyph.category = "mark"
