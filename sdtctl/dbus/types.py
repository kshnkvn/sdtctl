from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class DBusVariantValue:
    """Wrapper for D-Bus variant values.
    """

    value: int

    @classmethod
    def from_dbus_variant(cls, variant) -> Self:
        """Create instance from D-Bus variant.
        """
        if variant and hasattr(variant, 'value'):
            return cls(value=variant.value)
        return cls(value=0)
