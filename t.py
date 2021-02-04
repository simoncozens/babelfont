from nfsf.convertors import Convert

f = Convert("Truculenta[opsz,wdth,wght].glyphs").load()
f.save("output/GlyphsFileFormatv3.nfsf")
