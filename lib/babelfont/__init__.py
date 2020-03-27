import fontParts
import fontTools
import os
from babelfont.otf.font import OTFont
from babelfont.ttf.font import TTFont

def OpenFont(pathOrObject=None, showInterface=True):
  if os.path.isdir(pathOrObject):
      # It's probably a UFO
      return fontParts.fontshell.RFont(pathOrObject=pathOrObject, showInterface=showInterface)
  # But is it a TTF or an OTF? Trust the contents, not the extension
  try:
      f = fontTools.ttLib.TTFont(pathOrObject)
      if f.sfntVersion == "OTTO":
          return OTFont(pathOrObject=pathOrObject, showInterface=showInterface)
      else:
          return TTFont(pathOrObject=pathOrObject, showInterface=showInterface)
  except Exception as e:
      raise ValueError("Not a UFO, TTF or OTF file")