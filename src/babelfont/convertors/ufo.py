from babelfont import *
from babelfont.convertors.designspace import Designspace
from fontTools.designspaceLib import DesignSpaceDocument, SourceDescriptor
import ufoLib2


class UFO(Designspace):
    suffix = ".ufo"

    @classmethod
    def load(cls, convertor):
        self = cls()
        self.ufo = ufoLib2.Font.open(convertor.filename)
        # Wrap it in a DS
        self.ds = DesignSpaceDocument()
        s1 = SourceDescriptor()
        s1.path = convertor.filename
        s1.font = self.ufo
        s1.name = "master.ufo1"
        s1.familyName = self.ufo.info.familyName
        s1.styleName = self.ufo.info.styleName
        self.ds.addSource(s1)
        self.font = Font()
        return self._load()

    def _save(self):
        if len(self.font.masters) > 1:
            raise ValueError("Only single master fonts can be saved as UFO")
        self.save_master_to_ufo(self.font.masters[0], self.filename)
