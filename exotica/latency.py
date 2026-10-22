from __future__ import annotations

import time


async def measure_telegram_rtt(client, request=None) -> float:
    if request is None:
        from herokutl.tl.functions.updates import GetStateRequest

        request = GetStateRequest()

    started = time.perf_counter_ns()
    await client(request)
    return round((time.perf_counter_ns() - started) / 1_000_000, 1)
