"""Liebherr HomeAPI models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .const import ControlName, ControlType, ZonePosition


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
    control_name = ControlName.TEMPERATURE


@dataclass
class PresentationLightControlRequest(LiebherrControlRequest):
    """Control the presentation light intesity."""

    target: int
    control_name = ControlName.PRESENTATIONLIGHT


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
    control_name = ControlName.HYDROBREEZE


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
    control_name = ControlName.BIOFRESHPLUS


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
    control_name = ControlName.ICE_MAKER


@dataclass
class AutoDoorControl(LiebherrControlRequest):
    """Auto Door Control Request Model."""

    zoneId: int  # noqa: N815 pylint: disable=invalid-name
    value: bool  # True = open, False = close
    control_name = ControlName.AUTODOOR


@dataclass
class LiebherrControl:
    """Liebherr Control Model."""

    type: ControlType
    control_name: ControlName
    zoneId: int | None = None  # noqa: N815 pylint: disable=invalid-name
    zonePosition: ZonePosition | None = None  # noqa: N815 pylint: disable=invalid-name
    value: str | int | bool | None = None
    target: int | None = None
    min: int | None = None
    max: int | None = None
    currentMode: str | None = None  # noqa: N815 pylint: disable=invalid-name
    iceMakerMode: IceMakerControlRequest.IceMakerMode | None = None  # noqa: N815 pylint: disable=invalid-name
    supportedModes: list[str] | None = None  # noqa: N815 pylint: disable=invalid-name
    hasMaxIce: bool | None = None  # noqa: N815 pylint: disable=invalid-name
    temperatureUnit: str | None = None  # noqa: N815 pylint: disable=invalid-name
    measurement_unit: str | None = None

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
        if self.type == ControlType.BIO_FRESH_PLUS:
            return BioFreshPlusControlRequest.BioFreshPlusMode(self.currentMode)
        return HydroBreezeControlRequest.HydroBreezeMode(self.currentMode)

    @property
    def unit_of_measurement(self) -> str:
        """Fix the units for HA."""
        if self.measurement_unit is None or self.measurement_unit == "°C":
            return "°C"
        return "°F"

    @property
    def zone_id(self) -> int | None:
        """Translate key."""
        return self.zoneId

    @property
    def zone_position(self) -> ZonePosition | None:
        """Translate key."""
        return self.zonePosition


type ZoneID = int | None
type LiebherrZonedControls = dict[ZoneID, LiebherrControl]
type LiebherrControls = dict[ControlName, LiebherrControl | LiebherrZonedControls]


@staticmethod
def liebherr_controls_from_dict(
    controls: list[dict[str, Any]] | dict[str, Any],
) -> LiebherrControls:
    """Get mapping of controls from a list or a dictionary."""

    if not isinstance(controls, list):
        controls = [controls]
    new_controls: LiebherrControls = {}
    for dict_object in controls:
        if "name" in dict_object:
            dict_object["control_name"] = dict_object["name"]
            del dict_object["name"]
        if "unit" in dict_object:
            dict_object["measurement_unit"] = dict_object["unit"]
            del dict_object["unit"]
        control: LiebherrControl = LiebherrControl(**dict_object)
        if control.zone_id is not None:
            if control.control_name not in new_controls:
                new_controls[control.control_name] = {}
            new_controls[control.control_name][control.zone_id] = control
        else:
            new_controls[control.control_name] = control

    return new_controls


@dataclass
class LiebherrDevice:
    """Liebherr Device Model."""

    class DeviceType(StrEnum):
        """Device Types."""

        FRIDGE = "FRIDGE"
        FREEZER = "FREEZER"
        WINE = "WINE"
        COMBI = "COMBI"

    device_id: str
    name: str
    model: str
    image_url: str
    deviceType: DeviceType  # noqa: N815
    controls: LiebherrControls = field(default_factory=dict)
