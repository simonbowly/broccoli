import asyncio
import contextlib

import pytest

from broccoli.core import utils


@pytest.mark.asyncio
async def test_any_finished():
    fast = asyncio.Task(asyncio.sleep(0))
    slow = asyncio.Task(asyncio.sleep(60))
    await asyncio.sleep(0.1)
    fast_finished, slow_finished = await utils.any_finished(fast, slow)
    assert fast_finished and fast.done() and not fast.cancelled()
    assert not slow_finished and slow.done() and slow.cancelled()


@pytest.mark.asyncio
async def test_any_finished_shield():
    fast = asyncio.Task(asyncio.sleep(0))
    slow = asyncio.Task(asyncio.sleep(60))
    await asyncio.sleep(0.1)
    fast_finished, slow_finished = await utils.any_finished(fast, asyncio.shield(slow))
    assert fast_finished and not slow_finished
    assert fast.done() and not fast.cancelled()
    assert not slow.done()
    slow.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await slow


async def do_die():
    await asyncio.sleep(0.2)
    raise ValueError()


@pytest.mark.asyncio
async def test_any_finished_error():
    lives = asyncio.Task(asyncio.sleep(60))
    dies = asyncio.Task(do_die())
    await asyncio.sleep(0.1)
    lives_finished, dies_finished = await utils.any_finished(lives, dies)
    assert not lives_finished and lives.cancelled()
    assert dies_finished and dies.exception()
