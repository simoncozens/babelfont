from .BaseObject import BaseObject, I18NDictionary
from dataclasses import dataclass, field
import uuid
from fontTools.varLib.models import normalizeValue


@dataclass
class _AxisFields:
    name: I18NDictionary = field(
        metadata={"description": "The display name for this axis."}
    )
    tag: str = field(metadata={"description": "The four-letter axis tag."})
    id: str = field(
        default_factory=lambda: str(uuid.uuid1()),
        repr=False,
        metadata={
            "description": """An ID used to refer to this axis in the Master,
Layer and Instance `location` fields. (This is allows the user to change the
axis tag without the locations becoming lost.) If not provided, one will be
automatically generated on import from a UUID."""
        },
    )
    min: int = field(
        default=None, metadata={"description": "The minimum value of this axis."}
    )
    max: int = field(
        default=None, metadata={"description": "The maximum value of this axis."}
    )
    default: int = field(
        default=None,
        metadata={
            "description": """The default value of this axis (center of interpolation).
Note that if the min/max/default values are not supplied, they are returned as `None`
in the Python object, and should be computed from the master locations on export."""
        },
    )


@dataclass
class Axis(BaseObject, _AxisFields):
    """Represents an axis in a multiple master or variable font."""

    _write_one_line = True

    def __post_init__(self):
        # If they smacked my name with a bare string, replace with I18NDict
        if isinstance(self.name, str):
            self.name = I18NDictionary.with_default(self.name)

    def normalize_value(self, value):
        return normalizeValue(value, (self.min, self.default, self.max))
