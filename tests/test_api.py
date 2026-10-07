"""Unit tests for custom_components/intergas_xtend/api.py.

Two groups:

* Parser tests call ``XtendApi._parse_stats`` directly with a body string.
* Round-trip tests run ``XtendApi.async_get_stats`` against a small ``aiohttp.web``
  app started by the ``aiohttp_server`` fixture (pytest-aiohttp). The app listens on
  127.0.0.1, the only host the Home Assistant test plugin allows sockets for. The
  client is pointed at ``host:port`` of that server, so the request goes over a real
  TCP connection and the whole aiohttp path (timeout, status, body) is exercised.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
import json
from pathlib import Path

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer
import pytest

from custom_components.intergas_xtend import api as api_module
from custom_components.intergas_xtend.api import (
    XtendApi,
    XtendConnectionError,
    XtendResponseError,
)
from custom_components.intergas_xtend.const import STATS_FIELDS, STATS_PATH

FIXTURES = Path(__file__).resolve().parent / "fixtures"

Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]
ServerFactory = Callable[[Handler], Awaitable[TestServer]]


# --------------------------------------------------------------------------- #
# Parser                                                                       #
# --------------------------------------------------------------------------- #


def test_parse_fixture_returns_stats_unchanged() -> None:
    # Verify step of the parser item: 32 keys, firmware string stays a string.
    # The capture predates the statistics fields, so it is a subset of
    # STATS_FIELDS.
    body = (FIXTURES / "stats_values.json").read_text(encoding="utf-8")
    stats = XtendApi._parse_stats(body)
    assert isinstance(stats, dict)
    assert len(stats) == 32
    assert set(stats) < set(STATS_FIELDS)
    assert stats["47e0"] == "V1.20-"
    assert stats == json.loads(body)["stats"]


def test_parse_keeps_ints_and_sentinels_raw() -> None:
    # No scaling and no sentinel handling in api.py; that is the sensor layer.
    body = (FIXTURES / "stats_values.json").read_text(encoding="utf-8")
    stats = XtendApi._parse_stats(body)
    assert stats["79b3"] == 2641
    assert isinstance(stats["79b3"], int)
    assert stats["6206"] == 32767
    assert stats["7940"] == 255
    assert stats["8439"] == 0


@pytest.mark.parametrize(
    "body",
    [
        "not json",
        "",
        '{"stats": {',
    ],
)
def test_parse_invalid_json_raises_response_error(body: str) -> None:
    with pytest.raises(XtendResponseError):
        XtendApi._parse_stats(body)


@pytest.mark.parametrize(
    "body",
    [
        '{"other": {}}',
        "{}",
        '{"stats": null}',
        '{"stats": []}',
        '{"stats": "V1.20-"}',
        "[]",
        '"stats"',
        "42",
    ],
)
def test_parse_wrong_shape_raises_response_error(body: str) -> None:
    with pytest.raises(XtendResponseError):
        XtendApi._parse_stats(body)


# --------------------------------------------------------------------------- #
# HTTP round trip against a mocked device                                      #
# --------------------------------------------------------------------------- #


@pytest.fixture
async def session() -> AsyncIterator[aiohttp.ClientSession]:
    """Plain aiohttp session, the role Home Assistant's shared session plays."""
    async with aiohttp.ClientSession() as client_session:
        yield client_session


@pytest.fixture
def xtend_server(
    socket_enabled: None, aiohttp_server: Callable[..., Awaitable[TestServer]]
) -> ServerFactory:
    """Start a fake Xtend that answers GET /api/stats/values with ``handler``.

    The Home Assistant test plugin blocks sockets in every test. ``socket_enabled``
    (pytest-socket) lifts that for this test, the same way the plugin's own
    ``hass_client`` fixture does; the server only listens on 127.0.0.1.
    """

    async def _start(handler: Handler) -> TestServer:
        app = web.Application()
        app.router.add_get(STATS_PATH, handler)
        return await aiohttp_server(app)

    return _start


def _host(server: TestServer) -> str:
    # XtendApi builds ``http://{host}/...``; a host with a port works unchanged.
    return f"{server.host}:{server.port}"


def _text_handler(body: str, status: int = 200) -> Handler:
    async def handler(request: web.Request) -> web.Response:
        return web.Response(text=body, status=status)

    return handler


async def test_get_stats_returns_fixture_dict(
    session: aiohttp.ClientSession,
    xtend_server: ServerFactory,
    stats_payload: dict[str, int | str],
) -> None:
    body = (FIXTURES / "stats_values.json").read_text(encoding="utf-8")
    server = await xtend_server(_text_handler(body))

    stats = await XtendApi(session, _host(server)).async_get_stats()

    assert len(stats) == 32
    assert stats == stats_payload
    assert stats["47e0"] == "V1.20-"
    assert stats["79b3"] == 2641


async def test_get_stats_sends_all_fields_in_order(
    session: aiohttp.ClientSession, xtend_server: ServerFactory
) -> None:
    seen: list[web.Request] = []

    async def handler(request: web.Request) -> web.Response:
        seen.append(request)
        return web.Response(text='{"stats": {}}')

    server = await xtend_server(handler)
    await XtendApi(session, _host(server)).async_get_stats()

    assert len(seen) == 1
    request = seen[0]
    assert request.method == "GET"
    assert request.path == STATS_PATH
    assert request.query["fields"] == ",".join(STATS_FIELDS)
    assert request.query["fields"].split(",") == list(STATS_FIELDS)
    # Verify step of the statistics item: one request with all 55 ids.
    assert len(request.query["fields"].split(",")) == len(STATS_FIELDS) == 55


async def test_connection_refused_raises_connection_error(
    session: aiohttp.ClientSession, xtend_server: ServerFactory
) -> None:
    # Start a server only to get a port that is known to be free, then close it so
    # the next connect is refused. This is what happens once the AP is off.
    server = await xtend_server(_text_handler('{"stats": {}}'))
    host = _host(server)
    await server.close()

    with pytest.raises(XtendConnectionError):
        await XtendApi(session, host).async_get_stats()


async def test_timeout_raises_connection_error(
    session: aiohttp.ClientSession,
    xtend_server: ServerFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = asyncio.Event()

    async def handler(request: web.Request) -> web.Response:
        # Hold the response until the test releases it, so the client times out
        # and the server can still shut down quickly afterwards.
        await release.wait()
        return web.Response(text='{"stats": {}}')

    server = await xtend_server(handler)
    monkeypatch.setattr(api_module, "REQUEST_TIMEOUT", 0.1)
    try:
        with pytest.raises(XtendConnectionError):
            await XtendApi(session, _host(server)).async_get_stats()
    finally:
        release.set()


@pytest.mark.parametrize("status", [500, 404, 302])
async def test_non_200_status_raises_response_error(
    session: aiohttp.ClientSession, xtend_server: ServerFactory, status: int
) -> None:
    server = await xtend_server(_text_handler("Internal Server Error", status))

    with pytest.raises(XtendResponseError) as excinfo:
        await XtendApi(session, _host(server)).async_get_stats()
    assert str(status) in str(excinfo.value)


@pytest.mark.parametrize("body", ["not json", '{"other": {}}'])
async def test_bad_body_raises_response_error(
    session: aiohttp.ClientSession, xtend_server: ServerFactory, body: str
) -> None:
    server = await xtend_server(_text_handler(body))

    with pytest.raises(XtendResponseError):
        await XtendApi(session, _host(server)).async_get_stats()
