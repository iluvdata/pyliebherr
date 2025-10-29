"""The Liebherr Smart Device API."""

from dataclasses import asdict
import logging
from typing import Any

from aiohttp import ClientResponse, ClientSession

from .const import BASE_API_URL
from .exception import LiebherrAuthException, LiebherrFetchException
from .models import (
    LiebherrControl,
    LiebherrControlRequest,
    LiebherrDevice,
    liebherr_control_from_dict,
)

type ResponseData = list[dict[str, Any]]

_LOGGER = logging.getLogger(__package__)


async def _raise_for_error(response: ClientResponse) -> None:
    if response.status not in [200, 204]:
        _LOGGER.debug("Failed response text: %s", await response.text())
        if response.status == 401:
            _LOGGER.exception("API-KEY provided is not valid")
            raise LiebherrAuthException
        if response.status != 429:
            _LOGGER.exception("API rate limit exceeded")
            raise LiebherrFetchException(await response.json())
        _LOGGER.exception("Failed to fetch data @ path: %s", response.url.path)
        raise LiebherrFetchException(await response.json())


class LiebherrAPI:
    """Liebherr API Class."""

    def __init__(
        self, api_key: str, client_session: ClientSession | None = None
    ) -> None:
        """Initialize the Liebherr HomeAPI."""
        self._api_key: str = api_key
        self._session: ClientSession = (
            ClientSession() if client_session is None else client_session
        )

    async def _request(self, path: str = "", attempt: int = 0) -> ResponseData:
        _LOGGER.debug("Requesting data: /devices/%s", path)
        async with self._session.get(
            f"{BASE_API_URL}devices{path}", headers={"api-key": self._api_key}
        ) as response:
            if response.status != 429:
                await _raise_for_error(response)
            if response.status == 429:
                if attempt < 2:
                    _LOGGER.warning(
                        "Rate limit exceeded, retrying request (%d/2)", attempt + 1
                    )
                    return await self._request(path, attempt + 1)
                _LOGGER.exception("API rate limit exceeded after retries")
                raise LiebherrFetchException(await response.json())

            data: ResponseData = await response.json()
            _LOGGER.debug("Fetched data: %s", data)
            return data

    async def _post(self, path, payload: dict[str, Any]) -> ResponseData | None:
        _LOGGER.debug("Posting data to: /devices%s", path)
        async with self._session.post(
            f"{BASE_API_URL}devices{path}",
            json=payload,
            headers={
                "api-key": self._api_key,
                "Content-Type": "application/json",
            },
        ) as response:
            await _raise_for_error(response)
            if response.status == 204:
                # Success but no body is returned.
                return None
            data: ResponseData = await response.json()
            _LOGGER.debug("Posted data response: %s", data)
            return data

    async def async_get_appliances(self) -> list[LiebherrDevice]:
        """Retrieve the list of appliances."""

        data: ResponseData = await self._request()

        _LOGGER.debug("Fetched appliances: %s", data)
        return [
            LiebherrDevice(
                appliance["deviceId"],
                appliance.get("nickname", appliance["deviceName"]),
                appliance["deviceName"],
                appliance["imageUrl"],
                appliance["deviceType"],
                await self.async_get_controls(appliance["deviceId"]),
            )
            for appliance in data
        ]

    async def async_get_controls(self, device_id: str) -> list[LiebherrControl]:
        """Retrieve controls for a specific appliance."""

        response_object: list[LiebherrControl] | LiebherrControl = (
            liebherr_control_from_dict(await self._request(f"/{device_id}/controls"))
        )
        if not isinstance(response_object, list):
            return [response_object]
        return response_object

    async def async_set_value(
        self, device_id: str, control: LiebherrControlRequest
    ) -> ResponseData | None:
        """Activate or deactivate a control."""
        value: dict[str, Any] = asdict(control)
        del value["control_name"]

        return await self._post(f"/{device_id}/controls/{control.control_name}", value)

    async def async_close(self) -> None:
        """Close the aiohttp session."""
        await self._session.close()
