"""Testing module for API."""

import asyncio
import logging

from pyliebherr.api import LiebherrAPI

logging.basicConfig(level=logging.DEBUG)

_LOGGER = logging.getLogger(__name__)


async def __main__():
    """Main function to test the Liebherr API."""
    api: LiebherrAPI = LiebherrAPI("019e0f2983e19b80e9b1b30e9571c17f1ad52f085c")
    appliances = await api.async_get_appliances()
    print(appliances)
    await api.async_close()


asyncio.run(__main__())
