=========
babelfont
=========


.. image:: https://img.shields.io/pypi/v/babelfont.svg
        :target: https://pypi.python.org/pypi/babelfont

.. image:: https://img.shields.io/travis/simoncozens/babelfont.svg
        :target: https://travis-ci.com/simoncozens/babelfont

.. image:: https://readthedocs.org/projects/babelfont/badge/?version=latest
        :target: https://babelfont.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Read font files into `fontParts <http://fontparts.robotools.dev/>`_
objects and write them out again.

Usage
-----

Here's how to convert a font from one format to another::

    from babelfont import Babelfont

    font = Babelfont.open("My-Font.glyphs")
    font.save("My-Font.ufo")

To interact with the ``font`` object, see the `fontParts documentation <https://fontparts.robotools.dev/en/stable/objectref/objects/font.html>`_.

Currently Babelfont supports:

- UFO (Read and write)
- Glyphs (Read and write)
- OTF (Read only)
- TTF (Read only)

* Free software: Apache Software License 2.0
