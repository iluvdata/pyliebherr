"""Constants for the Liebherr API."""

from enum import StrEnum

BASE_URL = "https://home-api.smartdevice.liebherr.com"
API_VERSION = "/v1"
BASE_API_URL = f"{BASE_URL}{API_VERSION}/"


class CONTROL_TYPE(StrEnum): # pylint: disable=invalid-name
    """Liebherr Device Types."""

    TEMPERATURE = "TemperatureControl"
    ICE_MAKER = "IceMakerControl"
    BIO_FRESH_PLUS = "BioFreshPlusControl"
    AUTO_DOOR_CONTROL = "AutoDoorControl"
    HYDRO_BREEZE = "HydroBreezeControl"
    TOGGLE = "ToggleControl"
    PRESENTATION_LIGHT = "PresentationLightControl"
    IMAGE = "ImageControl"


class ZONE_POSITION(StrEnum): # pylint: disable=invalid-name
    """Liebherr Zone Positions."""

    TOP = "top"
    BOTTOM = "bottom"
    MIDDLE = "middle"
