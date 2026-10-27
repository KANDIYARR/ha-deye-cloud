"""Small, conservative async client for the Deye Cloud OpenAPI."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import time
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class DeyeCloudApiError(Exception):
    """Raised for authentication, transport, and API errors."""


class DeyeCloudApi:
    """Authenticated client with token caching and request throttling."""

    def __init__(self, hass, base_url: str, app_id: str, app_secret: str, email: str, password: str) -> None:
        self._hass = hass
        self._base_url = base_url.rstrip("/")
        self._app_id = app_id
        self._app_secret = app_secret
        self._email = email
        self._password = password
        self._session = None
        self._token: str | None = None
        self._token_expires = 0.0
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(timeout=ClientTimeout(total=API_TIMEOUT))
        return self._session

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _pace(self) -> None:
        # Stay far below the preliminary 60 requests/minute limit.
        delay = 1.1 - (time.monotonic() - self._last_request)
        if delay > 0:
            await asyncio.sleep(delay)
        self._last_request = time.monotonic()

    async def _request(self, path: str, *, body: dict | None = None, auth: bool = True, retry_auth: bool = True) -> dict:
        if auth and (not self._token or time.time() >= self._token_expires - 300):
            await self._authenticate()
        url = f"{self._base_url}/v1.0{path}"
        headers = {"Content-Type": "application/json"}
        if auth and self._token:
            headers["Authorization"] = self._token if self._token.lower().startswith("bearer ") else f"Bearer {self._token}"
        params = {"appId": self._app_id} if path == "/account/token" else None
        for attempt in range(4):
            await self._pace()
            try:
                session = await self._get_session()
                async with session.post(url, json=body or {}, params=params, headers=headers) as response:
                    if response.status == 401 and auth and retry_auth:
                        self._token = None
                        await self._authenticate()
                        headers["Authorization"] = self._token if self._token.lower().startswith("bearer ") else f"Bearer {self._token}"
                        continue
                    if response.status == 429 or response.status >= 500:
                        if attempt < 3:
                            retry_after = response.headers.get("Retry-After")
                            wait = float(retry_after) if retry_after and retry_after.isdigit() else min(60, 2 ** attempt + random.random())
                            await asyncio.sleep(wait)
                            continue
                    response.raise_for_status()
                    payload = await response.json(content_type=None)
            except (ClientError, asyncio.TimeoutError, ValueError) as err:
                if attempt < 3:
                    await asyncio.sleep(min(60, 2 ** attempt + random.random()))
                    continue
                raise DeyeCloudApiError(f"Deye Cloud request failed: {err}") from err
            if isinstance(payload, dict) and payload.get("success") is False:
                raise DeyeCloudApiError(str(payload.get("msg") or payload.get("code") or "Deye Cloud API error"))
            return payload
        raise DeyeCloudApiError("Deye Cloud request failed after retries")

    async def _authenticate(self) -> None:
        async with self._lock:
            if self._token and time.time() < self._token_expires - 300:
                return
            password_hash = await self._hass.async_add_executor_job(
                lambda: hashlib.sha256(self._password.encode()).hexdigest()
            )
            payload = await self._request(
                "/account/token",
                body={"appSecret": self._app_secret, "email": self._email, "password": password_hash},
                auth=False,
            )
            self._token = payload.get("accessToken")
            if not self._token:
                raise DeyeCloudApiError(str(payload.get("msg", "Authentication returned no access token")))
            self._token_expires = time.time() + int(payload.get("expiresIn", 3600))

    async def list_stations(self) -> list[dict[str, Any]]:
        payload = await self._request("/station/list", body={"page": 1, "size": 100})
        return payload.get("stationList", []) or payload.get("list", []) or []

    async def list_station_devices(self, station_id: int) -> list[dict[str, Any]]:
        payload = await self._request("/station/device", body={"page": 1, "size": 200, "stationIds": [station_id]})
        devices = payload.get("deviceListItems", []) or []
        total = int(payload.get("total", len(devices)))
        page = 2
        while len(devices) < total:
            next_page = await self._request("/station/device", body={"page": page, "size": 200, "stationIds": [station_id]})
            items = next_page.get("deviceListItems", []) or []
            if not items:
                break
            devices.extend(items)
            page += 1
        return devices

    async def latest_devices(self, serials: list[str]) -> list[dict[str, Any]]:
        if not serials:
            return []
        payload = await self._request("/device/latest", body={"deviceList": serials})
        return payload.get("deviceDataList", []) or []

    async def station_latest(self, station_id: int) -> dict[str, Any]:
        payload = await self._request("/station/latest", body={"stationId": station_id})
        return payload

    async def device_alerts(self, serial: str, start: int, end: int) -> list[dict[str, Any]]:
        payload = await self._request(
            "/device/alert/list",
            body={"deviceSn": serial, "startTimestamp": start, "endTimestamp": end, "page": 1, "size": 100},
        )
        return payload.get("alertList", []) or []
