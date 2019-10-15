import asyncio
import contextlib

import pytest

from broccoli.core import florets


@pytest.mark.asyncio
async def test_idle():
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(florets.idle(), timeout=0.2)


@pytest.mark.asyncio
async def test_stress():
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(florets.stress(cpus=2), timeout=0.2)
