from babelfont.convertors import Convert
import warnings


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "# [warning] %s\n" % (message)


warnings.formatwarning = warning_on_one_line

f = Convert("Nunito3.glyphs").load()
f.save("output/test.babelfont")
f.save("output/test.ttf")

