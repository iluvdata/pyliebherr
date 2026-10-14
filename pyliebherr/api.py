"""The Liebherr Smart Device API."""

import asyncio
from asyncio import Task, create_task
from collections.abc import Callable, Mapping
import json
import logging
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession
from aiohttp_sse_client2 import client as sse_client

from .const import BASE_API_URL
from .exception import (
    LiebherrAPILimitExceededException,
    LiebherrAuthException,
    LiebherrFetchException,
    LiebherrSSEException,
    LiebherrUpdateException,
)
from .models import LiebherrControlRequest, LiebherrDevice

type ResponseData = list[Mapping[str, Any]]

_LOGGER = logging.getLogger(__package__)


async def _raise_for_error(response: ClientResponse) -> None:
    if response.status not in [200, 204]:
        _LOGGER.debug("Failed response text: %s", response.text)
        if response.status == 401:
            raise LiebherrAuthException
        response_text: dict[str, str] = (
            await response.json()
            if response.headers["Content-Type"] == "application/json"
            else {"message": await response.text()}
        )
        if response.status == 429:
            raise LiebherrAPILimitExceededException(response_text.get("message"))
        if response.status == 504:
            response_text["message"] = "504 Gateway Timeout"
        if response.method == "POST":
            raise LiebherrUpdateException(response_text.get("message"))
        raise LiebherrFetchException(response_text.get("message"))


class LiebherrAPI:
    """Liebherr API Class."""

    def __init__(self, api_key: str, session: ClientSession) -> None:
        """Initialize the Liebherr HomeAPI."""
        self._session = session
        self._api_key = api_key
        self._sse_tasks: dict[str, Task[None]] = {}

    async def async_test_key(self) -> None:
        """Test the api key."""
        await self._request()

    def start_sse(self, device: LiebherrDevice, delay: float = 0) -> Callable[[], None]:
        """Register a callback function to call when SSE updates are received.

        Returns a cancel callback.
        """

        def _opened() -> None:
            """Log that connection is established."""
            _LOGGER.info("Connected %s to Liebherr SSE", device.device_id)

        async def connect_sse() -> None:
            if delay:
                await asyncio.sleep(delay)
            async with sse_client.EventSource(
                url=f"{BASE_API_URL}sse/devices/{device.device_id}/controls",
                session=self._session,
                headers={"api-key": self._api_key},
                on_open=_opened,
            ) as event_source:
                async for sse in event_source:
                    _LOGGER.debug(
                        "SSE: %s received with data %s", sse.message, sse.data
                    )
                    data = json.loads(sse.data)
                    device.updated(data if isinstance(data, list) else [data])

        task: Task[None] = create_task(
            connect_sse(),
            eager_start=True,
            name=f"Liebherr-{device.device_id}-SSE",
        )

        def _handle_task_result(task: Task[None]) -> None:
            if (not task.cancelled()) and (exc := task.exception()):
                _LOGGER.warning("%s error: %s", task.get_name(), str(exc))
                if device.device_id in self._sse_tasks:
                    del self._sse_tasks[device.device_id]
                device.error(
                    LiebherrSSEException(
                        f"SSE connection error for device {device.device_id}: {exc}",
                    )
                )
                return
            _LOGGER.warning(
                "%s %s", task.get_name(), "cancelled" if task.cancelled() else "ended"
            )

        task.add_done_callback(_handle_task_result)
        self._sse_tasks[device.device_id] = task

        def _cancel_task() -> None:
            task.cancel()
            if device.device_id in self._sse_tasks:
                del self._sse_tasks[device.device_id]

        return _cancel_task

    async def _request(self, path: str = "") -> ResponseData:
        _LOGGER.debug("Requesting data: /devices%s", path)
        response: ClientResponse
        try:
            async with self._session.get(
                f"{BASE_API_URL}devices{path}", headers={"api-key": self._api_key}
            ) as response:
                await _raise_for_error(response)
                data: ResponseData = await response.json()
                _LOGGER.debug("Fetched data: %s", data)
                return data
        except ClientError as exc:
            raise LiebherrFetchException(str(exc)) from exc

    async def _post(self, path, payload: dict[str, Any]) -> ResponseData | None:
        _LOGGER.debug("Posting data to: /devices%s", f"devices{path}")
        async with self._session.post(
            f"{BASE_API_URL}devices{path}",
            json=payload,
            headers={
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

    async def async_get_devices(self) -> list[LiebherrDevice]:
        """Retrieve the list of appliances."""

        data: ResponseData = await self._request()

        devices: list[LiebherrDevice] = []

        for device in data:
            liebherr_device: LiebherrDevice = LiebherrDevice.model_validate(device)
            self.start_sse(liebherr_device)
            devices.append(liebherr_device)
        return devices

    async def async_get_devices_wait_for_controls(
        self,
        timeout: float = 30,
    ) -> list[LiebherrDevice]:
        """Get devices and wait for first SSE."""

        async def wait_for_first_sse(device: LiebherrDevice) -> None:
            while not device.available:
                await asyncio.sleep(1)

        devices: list[LiebherrDevice] = await self.async_get_devices()

        async with asyncio.timeout(timeout), asyncio.TaskGroup() as tg:
            for device in devices:
                tg.create_task(wait_for_first_sse(device))

        return devices

    async def async_set_value(
        self, device_id: str, control: LiebherrControlRequest
    ) -> ResponseData | None:
        """Activate or deactivate a control."""
        value: dict[str, Any] = control.model_dump(by_alias=True)
        del value["controlName"]

        return await self._post(f"/{device_id}/controls/{control.control_name}", value)

    async def async_close(self) -> None:
        """Close the aiohttp session."""
        for task in self._sse_tasks.values():
            task.cancel()
