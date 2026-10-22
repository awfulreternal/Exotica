import asyncio

from exotica.latency import measure_telegram_rtt


def test_measure_telegram_rtt_sends_exactly_one_rpc():
    requests = []

    class FakeClient:
        async def __call__(self, request):
            requests.append(request)

    marker = object()
    elapsed = asyncio.run(measure_telegram_rtt(FakeClient(), marker))

    assert requests == [marker]
    assert elapsed >= 0
