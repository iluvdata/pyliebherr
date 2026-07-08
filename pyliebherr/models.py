"""Liebherr HomeAPI models."""

from collections.abc import Callable, Mapping
from enum import StrEnum
from typing import Annotated, Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, PlainSerializer
from pydantic.alias_generators import to_camel

from .const import ControlName, ControlType, TempUnit, ZonePosition
from .exception import LiebherrSSEException

MODEL_CONFIG: ConfigDict = ConfigDict(alias_generator=to_camel)


class LiebherrControlRequest(BaseModel):
    """Liebherr Control Model."""

    model_config = MODEL_CONFIG

    control_name: str


class ZonedControlRequest(LiebherrControlRequest):
    """Zoned control request model."""

    zone_id: int


class TemperatureControlRequest(ZonedControlRequest):
    """Temperature Control Request Model."""

    target: int
    unit: TempUnit  # '°C' or '°F'
    control_name: str = Field(ControlName.TEMPERATURE)


class PresentationLightControlRequest(LiebherrControlRequest):
    """Control the presentation light intensity."""

    target: int
    control_name: str = Field(ControlName.PRESENTATIONLIGHT)


class BaseToggleControlRequest(LiebherrControlRequest):
    """Base Toggle Control Request Model."""

    value: bool


class ZoneToggleControlRequest(BaseToggleControlRequest, ZonedControlRequest):
    """Zone Toggle Control Request Model."""


class HydroBreezeControlRequest(ZonedControlRequest):
    """HydroBreeze Control."""

    class HydroBreezeMode(StrEnum):
        """Accepted Hydrobreeze Modes."""

        OFF = "OFF"
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"

    hydro_breeze_mode: HydroBreezeMode
    zone_id: int
    control_name: str = Field(ControlName.HYDROBREEZE)


class BioFreshPlusControlRequest(LiebherrControlRequest):
    """BiofreshPlusControl."""

    class BioFreshPlusMode(StrEnum):
        """Biofresh modes."""

        ZERO_ZERO = "ZERO_ZERO"
        ZERO_MINUS_TWO = "ZERO_MINU_TWO"
        MINUS_TWO_MINUS_TWO = "MINUS_TWO_MINUS_TWO"
        MINUS_TWO_ZERO = "MINUS_TWO_ZERO"

    bio_fresh_plus_mode: BioFreshPlusMode
    control_name: str = Field(ControlName.BIOFRESHPLUS)


class IceMakerControlRequest(ZonedControlRequest):
    """Ice Maker Control Request Model."""

    class IceMakerMode(StrEnum):
        """Ice Maker Modes."""

        OFF = "OFF"
        ON = "ON"
        MAX_ICE = "MAX_ICE"

    ice_maker_mode: IceMakerMode
    control_name: str = Field(ControlName.ICE_MAKER)


class AutoDoorControlRequest(ZonedControlRequest):
    """Auto Door Control Request Model."""

    value: bool  # True = open, False = close
    control_name: str = Field(ControlName.AUTODOOR)


class LiebherrControl(BaseModel):
    """Liebherr Control Model."""

    model_config = MODEL_CONFIG

    type: ControlType
    control: ControlName = Field(validation_alias="name", serialization_alias="name")
    zone_id: int | None = None
    zone_position: ZonePosition | None = None
    value: str | int | bool | None = None
    target: int | None = None
    min: int | None = None
    max: int | None = None
    mode: str | None = Field(
        validation_alias="currentMode", serialization_alias="currentMode", default=None
    )
    ice_maker_mode: IceMakerControlRequest.IceMakerMode | None = None
    supported_modes: list[str] | None = None
    has_max_ice: bool | None = None
    measurement_unit: TempUnit | None = Field(
        validation_alias=AliasChoices("unit", "temperatureUnit"),
        serialization_alias="unit",
        default=None,
    )
    temp_steps: list[int] = Field(
        validation_alias="setTemperatureSteps",
        serialization_alias="setTemperatureSteps",
        default=[],
    )
    use_temp_steps: bool = Field(
        False,
        validation_alias="setTemperatureStepsEnabled",
        serialization_alias="setTemperatureStepsEnabled",
    )

    update_callback: Callable[[], None] | None = Field(None, exclude=True)

    def updated(self) -> None:
        """Update received via Device."""
        if callable(self.update_callback):
            self.update_callback()

    @property
    def control_name(self) -> str:
        """Get control name."""
        return self.control or self.type

    @property
    def current_mode(
        self,
    ) -> (
        HydroBreezeControlRequest.HydroBreezeMode
        | BioFreshPlusControlRequest.BioFreshPlusMode
        | None
    ):
        """Get the mode."""
        if self.mode is None:
            return None
        if self.type == ControlType.BIO_FRESH_PLUS:
            return BioFreshPlusControlRequest.BioFreshPlusMode(self.mode)
        return HydroBreezeControlRequest.HydroBreezeMode(self.mode)

    @current_mode.setter
    def current_mode(self, value: str) -> None:
        """Set the mode."""
        self.mode = value

    @property
    def unit_of_measurement(self) -> TempUnit:
        """Fix the units for HA."""
        return (
            TempUnit.CELSIUS
            if self.measurement_unit is None
            or self.measurement_unit == TempUnit.CELSIUS
            else TempUnit.FAHRENHEIT
        )


LiebherrControlKey = tuple[ControlName, int | None]
LiebherrControls = dict[LiebherrControlKey, LiebherrControl]


class LiebherrDevice(BaseModel):
    """Liebherr Device Model."""

    model_config = MODEL_CONFIG

    class DeviceType(StrEnum):
        """Device Types."""

        FRIDGE = "FRIDGE"
        FREEZER = "FREEZER"
        WINE = "WINE"
        COMBI = "COMBI"

    device_id: str
    name: str = Field(validation_alias="nickname")
    model: str = Field(validation_alias="deviceName")
    image_url: str
    device_type: DeviceType
    controls: Annotated[
        LiebherrControls,
        PlainSerializer(lambda x: list(x.values()), return_type=list[LiebherrControl]),
    ] = Field(default_factory=dict)

    # Excluded from serialization
    available: bool = Field(False, exclude=True)
    update_callback: Callable[[LiebherrDevice], None] | None = Field(None, exclude=True)
    error_callbacks: list[Callable[[LiebherrSSEException], None]] = Field(
        default_factory=list, exclude=True
    )
    reconnect_attempt: int = Field(0, exclude=True)

    def add_error_callback(
        self, error_callback: Callable[[LiebherrSSEException], None]
    ) -> None:
        """Add an error callback to call on errors."""
        self.error_callbacks.append(error_callback)

    def updated(self, data: list[Mapping[str, Any]]) -> None:
        """Update received via SSE."""
        self._update_controls(data)
        self.available = True
        self.reconnect_attempt = 0
        if callable(self.update_callback):
            self.update_callback(self)

    def error(self, exc: LiebherrSSEException) -> None:
        """Error received via SSE."""
        self.available = False
        self.reconnect_attempt += 1
        for error_callback in self.error_callbacks:
            error_callback(exc)

    def _update_controls(self, controls: list[Mapping[str, Any]]) -> None:
        """Get mapping of controls from a list or a dictionary."""

        for dict_object in controls:
            control: LiebherrControl = LiebherrControl.model_validate(dict_object)

            control_key: LiebherrControlKey = (
                ControlName(control.control_name),
                control.zone_id,
            )

            if self.controls.get(control_key):  # pylint: disable=no-member
                control.update_callback = self.controls[control_key].update_callback
                self.controls[control_key] = control
                self.controls[control_key].updated()
            else:
                self.controls[control_key] = control
