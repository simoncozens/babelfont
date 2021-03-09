from babelfont import *
from babelfont.convertors import BaseConvertor
from fontTools.designspaceLib import DesignSpaceDocument
import defcon
import uuid


class Designspace(BaseConvertor):
    suffix = ".designspace"

    @classmethod
    def load(cls, convertor):
        self = cls()
        self.ds = DesignSpaceDocument.fromfile(convertor.filename)
        self.ds.loadSourceFonts(defcon.Font)
        self.font = Font()
        return self._load()

    def _load(self):
        self._load_axes()

        glyphs_dict = {}

        for source in self.ds.sources:
            source._nfsf_master = self._load_master(source)
            self.font.masters.append(source._nfsf_master)

        for instance in self.ds.instances:
            self.font.instances.append(self._load_instance(instance))

        self._load_metadata()

        # Load glyphs from the first master, because everything is awful
        for g in self.ds.sources[0].font.glyphOrder:
            glyphs_dict[g] = self._load_glyph(self.ds.sources[0].font[g])
            self.font.glyphs.append(glyphs_dict[g])

        # Right, let's find all the layers. This will be messy.
        for source in self.ds.sources:
            for ufo_layer in source.font.layers:
                for g in source.font.glyphOrder:
                    if g not in glyphs_dict:
                        import warnings
                        warnings.warn("Incompatible glyph set: %s appears in %s but is not in default" % (g, source.filename))
                        continue
                    if g not in ufo_layer:
                        continue
                    glyphs_dict[g].layers.append(self._load_layer(source, ufo_layer, g))

        return self.font

    def _load_axes(self):
        for a in self.ds.axes:
            self.font.axes.append(
                Axis(
                    name=a.name,
                    tag=a.tag,
                    min=a.minimum,
                    max=a.maximum,
                    default=a.default,
                    map=a.map
                )
            )

    def _load_master(self, source):
        i = source.font.info
        master = Master(
            name=source.name,
            id=(source.name or uuid.uuid1()),
        )
        for metric in Master.CORE_METRICS:
            master.metrics[metric]=getattr(i, metric)
        _axis_name_to_id = {
            a.name.get_default(): a.tag for a in self.font.axes
        }
        master.location = { _axis_name_to_id[k]: v for k,v in source.location.items() }
        master.font = self.font
        assert master.valid
        return master

    def _load_glyph(self, ufo_glyph):
        cp = ufo_glyph.unicodes or [ufo_glyph.unicode]
        category = (
            self.ds.sources[0]
            .font.lib.get("public.openTypeCategories", {})
            .get(ufo_glyph.name, "base")
        )
        g = Glyph(name=ufo_glyph.name, codepoints=cp, category=category)
        return g

    def _load_layer(self, source, ufo_layer, glyphname):
        ufo_glyph = ufo_layer[glyphname]
        width = ufo_glyph.width
        l = Layer(width=width, id=uuid.uuid1())
        l._master = source._nfsf_master.id
        l._font = self.font
        # XXX load shapes, anchors, metrics, etc.
        for contour in ufo_glyph:
            l.shapes.append(self._load_contour(contour))
        assert l.valid
        return l

    def _load_contour(self, contour):
        shape = Shape()
        shape.nodes = []
        for p in contour:
            if p.segmentType == "move":
                p.segmentType = "line"
            ourtype = Node._from_pen_type[p.segmentType]
            if p.smooth:
                ourtype = ourtype + "s"
            shape.nodes.append(Node(p.x, p.y, ourtype))
        return shape

    def _load_instance(self, ufo_instance):
        instance = Instance(name=ufo_instance.name, location=ufo_instance.location)
        return instance

    def _load_metadata(self):
        firstfontinfo = self.ds.sources[0].font.info
        self.font.names.familyName.set_default(firstfontinfo.familyName)
        self.font.upm = firstfontinfo.unitsPerEm
        self.font.version = (firstfontinfo.versionMajor, firstfontinfo.versionMinor)
        self.font.note = firstfontinfo.note
