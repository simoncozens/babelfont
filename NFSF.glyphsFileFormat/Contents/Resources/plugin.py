# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
import sys
import os

sys.path.insert(0, "/Users/simon/hacks/typography/nfsf/src")
from babelfont.convertors.gsobject import GSObject
from babelfont import Font

class NFSFExport(FileFormatPlugin):
    # The NSView object from the User Interface. Keep this here!
    dialog = objc.IBOutlet()

    @objc.python_method
    def settings(self):
        self.name = "NFSF"
        self.icon = "ExportIcon"
        self.toolbarPosition = 100
        # Load .nib dialog (with .extension)
        # self.loadNib("IBdialog", __file__)

    # @objc.python_method
    # def start(self):
    #   pass

    @objc.python_method
    def export(self, font):
        # Ask for export destination and write the file:
        title = "Choose export destination"
        proposedFilename = font.familyName
        fileTypes = ["nfsf"]
        # Call dialog
        filepath = GetSaveFile(title, proposedFilename, fileTypes)

        if filepath:
            f = GSObject()
            f.scratch = {"gsfont": font}
            f.font = Font()
            f.gsfont = font
            f._load()
            f.font.save(filepath)
            return (
                True,
                'The export of "%s" was successful.' % (os.path.basename(filepath)),
            )

        else:
            return (False, "No file chosen")

    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
