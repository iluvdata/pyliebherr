"""Liebherr HomeAPI models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .const import CONTROL_TYPE, ZONE_POSITION


@dataclass
class LiebherrControlRequest:
    """Liebherr Control Model."""

    control_name: str = field(init=False)


@dataclass
class TemperatureControlRequest(LiebherrControlRequest):
    """Temperature Control Request Model."""

    zoneId: int  # noqa: N815 pylint: disable=invalid-name
    target: int
    unit: str  # '°C' or '°F'
    control_name = "temperature"


@dataclass
class PresentationLightControlRequest(LiebherrControlRequest):
    """Control the presentation light intesity."""

    target: int
    control_name = "presentationlight"


@dataclass
class BaseToggleControlRequest(LiebherrControlRequest):
    """Base Toggle Control Request Model."""

    value: bool


@dataclass
class ZoneToggleControlRequest(BaseToggleControlRequest):
    """Zone Toggle Control Request Model."""

    zoneId: int  # noqa: N815 pylint: disable=invalid-name


@dataclass
class HydroBreezeControlRequest(LiebherrControlRequest):
    """HydroBreeze Control."""

    class HydroBreezeMode(StrEnum):
        """Accepted Hydrobreeze Modes."""

        OFF = "OFF"
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"

    hydroBreezeMode: HydroBreezeMode  # noqa: N815 pylint: disable=invalid-name
    zoneId: int  # noqa: N815 pylint: disable=invalid-name
    control_name = "hydrobreeze"


@dataclass
class BioFreshPlusControlRequest(LiebherrControlRequest):
    """BiofreshPlusControl."""

    class BioFreshPlusMode(StrEnum):
        """Biofresh modes."""

        ZERO_ZERO = "ZERO_ZERO"
        ZERO_MINUS_TWO = "ZERO_MINU_TWO"
        MINUS_TWO_MINUS_TWO = "MINUS_TWO_MINUS_TWO"
        MINUS_TWO_ZERO = "MINUS_TWO_ZERO"

    bioFreshPlusMode: BioFreshPlusMode  # noqa: N815 pylint: disable=invalid-name
    zoneId: int  # noqa: N815 pylint: disable=invalid-name
    control_name = "biofreshplus"


@dataclass
class IceMakerControlRequest(LiebherrControlRequest):
    """Ice Maker Control Request Model."""

    class IceMakerMode(StrEnum):
        """Ice Maker Modes."""

        OFF = "OFF"
        ON = "ON"
        MAX_ICE = "MAX_ICE"

    zoneId: int  # noqa: N815 pylint: disable=invalid-name
    iceMakerMode: IceMakerMode  # noqa: N815 pylint: disable=invalid-name
    control_name = "icemaker"


@dataclass
class AutoDoorControl(LiebherrControlRequest):
    """Auto Door Control Request Model."""

    zoneId: int  # noqa: N815 pylint: disable=invalid-name
    value: bool  # True = open, False = close
    control_name = "autodoor"


@dataclass
class LiebherrControl:
    """Liebherr Control Model."""

    type: CONTROL_TYPE
    control_name: str
    zoneId: int | None = None  # noqa: N815 pylint: disable=invalid-name
    zonePosition: ZONE_POSITION | None = None  # noqa: N815 pylint: disable=invalid-name
    value: bool | int | None = None
    target: int | None = None
    min: int | None = None
    max: int | None = None
    currentMode: str | None = None  # noqa: N815 pylint: disable=invalid-name
    iceMakerMode: IceMakerControlRequest.IceMakerMode | None = None  # noqa: N815 pylint: disable=invalid-name
    supportedModes: list[str] | None = None  # noqa: N815 pylint: disable=invalid-name
    hasMaxIce: bool | None = None  # noqa: N815 pylint: disable=invalid-name
    temperatureUnit: str | None = None  # noqa: N815 pylint: disable=invalid-name
    u_measure: str | None = None

    @property
    def name(self) -> str:
        """Get control name."""
        return self.name if self.name else self.type

    @property
    def current_mode(
        self,
    ) -> (
        HydroBreezeControlRequest.HydroBreezeMode
        | BioFreshPlusControlRequest.BioFreshPlusMode
        | None
    ):
        """Get the mode."""
        if self.currentMode is None:
            return None
        if self.type == CONTROL_TYPE.BIO_FRESH_PLUS:
            return BioFreshPlusControlRequest.BioFreshPlusMode(self.currentMode)
        return HydroBreezeControlRequest.HydroBreezeMode(self.currentMode)

    @property
    def unit_of_measurement(self) -> str:
        """Fix the units for HA."""
        if self.u_measure is None or self.u_measure == "°C":
            return "°C"
        return "°F"

    @property
    def zone_id(self) -> int:
        """Translate key."""
        return self.zoneId if self.zoneId is not None else 0

    @property
    def zone_position(self) -> ZONE_POSITION | None:
        """Translate key."""
        return self.zonePosition


@staticmethod
def liebherr_control_from_dict(
    control: list[dict[str, Any]] | dict[str, Any],
) -> list[LiebherrControl] | LiebherrControl:
    """Get a control from a list or a dictionary."""

    if isinstance(control, list):
        new_list: list[LiebherrControl] = []
        for dict_object in control:
            if "name" in dict_object:
                dict_object["control_name"] = dict_object["name"]
                del dict_object["name"]
            if "unit" in dict_object:
                dict_object["u_measure"] = dict_object["unit"]
                del dict_object["unit"]
            new_list.append(LiebherrControl(**dict_object))
        return new_list
    if "name" in control:
        control["control_name"] = control["name"]
        del control["name"]
    if "unit" in control:
        control["u_measure"] = control["unit"]
        del control["unit"]
    return LiebherrControl(**control)


@dataclass
class LiebherrDevice:
    """Liebherr Device Model."""

    class Type(StrEnum):
        """Device Types."""

        FRIDGE = "FRIDGE"
        FREEZER = "FREEZER"
        WINE = "WINE"
        COMBI = "COMBI"

    device_id: str
    name: str
    model: str
    image_url: str
    type: Type
    controls: list[LiebherrControl]
