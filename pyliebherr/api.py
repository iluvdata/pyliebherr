"""The Liebherr Smart Device API."""

import asyncio
from asyncio import Task, create_task
from collections.abc import Callable, Mapping
import logging
from ssl import SSLContext
from typing import Any

from httpx import AsyncClient, Response, Timeout
from httpx_sse import aconnect_sse

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


def _raise_for_error(response: Response) -> None:
    if response.status_code not in [200, 204]:
        _LOGGER.debug("Failed response text: %s", response.text)
        if response.status_code == 401:
            raise LiebherrAuthException
        response_text: str | dict[str, str] = (
            response.json() if response.request.method != "HEAD" else ""
        )
        if response.status_code == 429:
            raise LiebherrAPILimitExceededException(response_text)
        if response.request.method == "POST":
            raise LiebherrUpdateException(response_text)
        raise LiebherrFetchException(response_text)


class LiebherrAPI:
    """Liebherr API Class."""

    def __init__(self, api_key: str, ssl_context: SSLContext | None = None) -> None:
        """Initialize the Liebherr HomeAPI."""
        self._client: AsyncClient
        self._sse_tasks: dict[str, Task[None]] = {}
        if ssl_context is None:
            self._client = AsyncClient(
                timeout=Timeout(60, read=None),
                headers={"api-key": api_key},
                base_url=f"{BASE_API_URL}",
            )
        else:
            self._client = AsyncClient(
                timeout=Timeout(60, read=None),
                headers={"api-key": api_key},
                base_url=f"{BASE_API_URL}",
                verify=ssl_context,
            )

    async def async_test_key(self) -> None:
        """Test the api key."""
        await self._request()

    def start_sse(self, device: LiebherrDevice, delay: float = 0) -> Callable[[], None]:
        """Register a callback function to call when SSE updates are received.

        Returns a cancel callback.
        """

        async def connect_sse() -> None:
            if delay:
                await asyncio.sleep(delay)
            async with aconnect_sse(
                self._client,
                "GET",
                f"sse/devices/{device.device_id}/controls",
            ) as event_source:
                event_source.response.raise_for_status()
                _LOGGER.info("Connected %s to Liebherr SSE", device.device_id)

                async for sse in event_source.aiter_sse():
                    _LOGGER.debug("SSE: %s received with data %s", sse.event, sse.data)

                    data: ResponseData = sse.json()

                    device.updated(data)

        task: Task[None] = create_task(
            connect_sse(),
            eager_start=True,  # py # pyright: ignore[reportCallIssue]
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
        response: Response = await self._client.get(f"devices{path}")
        _raise_for_error(response)
        data: ResponseData = response.json()
        _LOGGER.debug("Fetched data: %s", data)
        return data

    async def _post(self, path, payload: dict[str, Any]) -> ResponseData | None:
        _LOGGER.debug("Posting data to: /devices%s", f"devices{path}")
        response: Response = await self._client.post(
            f"devices{path}",
            json=payload,
            headers={
                "Content-Type": "application/json",
            },
        )
        _raise_for_error(response)
        if response.status_code == 204:
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
        timeout: float = 10,
    ) -> list[LiebherrDevice]:
        """Get devices and wait for first SSE."""

        async def wait_for_first_sse(device: LiebherrDevice) -> None:
            while not device.available:
                await asyncio.sleep(0.5)

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
        await self._client.aclose()
