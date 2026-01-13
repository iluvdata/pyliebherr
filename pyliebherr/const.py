"""Constants for the Liebherr API."""

from enum import StrEnum

BASE_URL = "https://home-api.smartdevice.liebherr.com"
API_VERSION = "v1"
BASE_API_URL = f"{BASE_URL}/{API_VERSION}/"


class ControlType(StrEnum):
    """Liebherr Control Type."""

    TEMPERATURE = "TemperatureControl"
    ICE_MAKER = "IceMakerControl"
    BIO_FRESH_PLUS = "BioFreshPlusControl"
    AUTO_DOOR_CONTROL = "AutoDoorControl"
    HYDRO_BREEZE = "HydroBreezeControl"
    TOGGLE = "ToggleControl"
    PRESENTATION_LIGHT = "PresentationLightControl"
    IMAGE = "ImageControl"
    UPDATED = "UpdatedControl"


class ControlName(StrEnum):
    """Liebherr Control Types."""

    ICE_MAKER = "icemaker"
    NIGHTMODE = "nightmode"
    PARTYMODE = "partymode"
    SUPERCOOL = "supercool"
    SUPERFROST = "superfrost"
    TEMPERATURE = "temperature"
    AUTODOOR = "autodoor"
    BIOFRESHPLUS = "biofreshplus"
    HYDROBREEZE = "hydrobreeze"
    PRESENTATIONLIGHT = "presentationlight"


CONTROL_NAMES: dict[ControlType, set[ControlName]] = {
    ControlType.AUTO_DOOR_CONTROL: {ControlName.AUTODOOR},
    ControlType.BIO_FRESH_PLUS: {ControlName.BIOFRESHPLUS},
    ControlType.HYDRO_BREEZE: {ControlName.BIOFRESHPLUS},
    ControlType.ICE_MAKER: {ControlName.ICE_MAKER},
    ControlType.PRESENTATION_LIGHT: {ControlName.PRESENTATIONLIGHT},
    ControlType.TEMPERATURE: {ControlName.TEMPERATURE},
    ControlType.TOGGLE: {
        ControlName.NIGHTMODE,
        ControlName.PARTYMODE,
        ControlName.SUPERCOOL,
        ControlName.SUPERFROST,
    },
}


class ZonePosition(StrEnum):
    """Liebherr Zone Positions."""

    TOP = "top"
    BOTTOM = "bottom"
    MIDDLE = "middle"
