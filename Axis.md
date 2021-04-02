---
title: Axis
---
Represents an axis in a multiple master or variable font.
* When writing to NFSF-JSON, this class must be serialized without newlines
## Axis.name

* Python type: `I18NDictionary`

* **Required field**

The display name for this axis. *Localizable.*


## Axis.tag

* Python type: `str`

* **Required field**

The four-letter axis tag.


## Axis.id

* Python type: `str`

An ID used to refer to this axis in the Master,
Layer and Instance `location` fields. (This is allows the user to change the
axis tag without the locations becoming lost.) If not provided, one will be
automatically generated on import from a UUID.


## Axis.min

* Python type: `int`

The minimum value of this axis, in user space coordinates.
*If not provided, defaults to* `None`.


## Axis.max

* Python type: `int`

The maximum value of this axis, in user space coordinates.
*If not provided, defaults to* `None`.


## Axis.default

* Python type: `int`

The default value of this axis (center of interpolation),
in user space coordinates. Note that if the min/max/default values are not supplied,
they are returned as `None` in the Python object, and should be computed from the
master locations on export.
*If not provided, defaults to* `None`.


## Axis.map

* Python type: `[(int, int)]`

The mapping between userspace and designspace coordinates.
*If not provided, defaults to* `None`.


## Axis._formatspecific

* Python type: `dict`


Each object in NFSF has an optional attached dictionary to allow the storage
of format-specific information. Font creation software may store any additional
information that they wish to have preserved on import and export under a
namespaced (reverse-domain) key in this dictionary. For example, information
specific to the Glyphs software should be stored under the key `com.glyphsapp`.
The value stored under this key may be any data serializable in JSON; typically
it will be a `dict`.

Note that there is an important distinction between the Python object format
of this field and the NFSF-JSON representation. When stored to JSON, this key
is exported not as `_formatspecific` but as a simple underscore (`_`).



