"""Liebherr HomeAPI models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from dataclasses_json import LetterCase, config, dataclass_json

from .const import ControlName, ControlType, ZonePosition


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class LiebherrControlRequest:
    """Liebherr Control Model."""

    control_name: str = field(init=False)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TemperatureControlRequest(LiebherrControlRequest):
    """Temperature Control Request Model."""

    zone_id: int
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


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ZoneToggleControlRequest(BaseToggleControlRequest):
    """Zone Toggle Control Request Model."""

    zone_id: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class HydroBreezeControlRequest(LiebherrControlRequest):
    """HydroBreeze Control."""

    class HydroBreezeMode(StrEnum):
        """Accepted Hydrobreeze Modes."""

        OFF = "OFF"
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"

    hydro_breeze_mode: HydroBreezeMode
    zone_id: int
    control_name = ControlName.HYDROBREEZE


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class BioFreshPlusControlRequest(LiebherrControlRequest):
    """BiofreshPlusControl."""

    class BioFreshPlusMode(StrEnum):
        """Biofresh modes."""

        ZERO_ZERO = "ZERO_ZERO"
        ZERO_MINUS_TWO = "ZERO_MINU_TWO"
        MINUS_TWO_MINUS_TWO = "MINUS_TWO_MINUS_TWO"
        MINUS_TWO_ZERO = "MINUS_TWO_ZERO"

    bio_fresh_plus_mode: BioFreshPlusMode
    zone_id: int
    control_name = ControlName.BIOFRESHPLUS


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class IceMakerControlRequest(LiebherrControlRequest):
    """Ice Maker Control Request Model."""

    class IceMakerMode(StrEnum):
        """Ice Maker Modes."""

        OFF = "OFF"
        ON = "ON"
        MAX_ICE = "MAX_ICE"

    zone_id: int
    ice_maker_mode: IceMakerMode
    control_name = ControlName.ICE_MAKER


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AutoDoorControl(LiebherrControlRequest):
    """Auto Door Control Request Model."""

    zone_id: int
    value: bool  # True = open, False = close
    control_name = ControlName.AUTODOOR


type ZoneID = int | None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class LiebherrControl:
    """Liebherr Control Model."""

    type: ControlType
    _control_name: ControlName = field(metadata=config(field_name="name"))
    zone_id: ZoneID | None = None
    zone_position: ZonePosition | None = None
    value: str | int | bool | None = None
    target: int | None = None
    min: int | None = None
    max: int | None = None
    _current_mode: str | None = field(
        default=None, metadata=config(field_name="currentMode")
    )
    ice_maker_mode: IceMakerControlRequest.IceMakerMode | None = None
    supported_modes: list[str] | None = None
    has_max_ice: bool | None = None
    temperature_unit: str | None = None
    _measurement_unit: str | None = field(
        default=None, metadata=config(field_name="unit")
    )

    @property
    def control_name(self) -> str:
        """Get control name."""
        return self._control_name if self._control_name else self.type

    @property
    def current_mode(
        self,
    ) -> (
        HydroBreezeControlRequest.HydroBreezeMode
        | BioFreshPlusControlRequest.BioFreshPlusMode
        | None
    ):
        """Get the mode."""
        if self._current_mode is None:
            return None
        if self.type == ControlType.BIO_FRESH_PLUS:
            return BioFreshPlusControlRequest.BioFreshPlusMode(self._current_mode)
        return HydroBreezeControlRequest.HydroBreezeMode(self._current_mode)

    @property
    def unit_of_measurement(self) -> str:
        """Fix the units for HA."""
        return (
            "°C"
            if self._measurement_unit is None or self._measurement_unit == "°C"
            else "°F"
        )


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
        control: LiebherrControl = LiebherrControl.from_dict(dict_object)
        if control.zone_id is not None:
            if control.control_name not in new_controls:
                new_controls[control.control_name] = {}
            new_controls[control.control_name][control.zone_id] = control
        else:
            new_controls[control.control_name] = control

    return new_controls


@dataclass_json(letter_case=LetterCase.CAMEL)
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
    name: str = field(metadata=config(field_name="nickname"))
    model: str = field(metadata=config(field_name="deviceName"))
    image_url: str
    device_type: DeviceType
