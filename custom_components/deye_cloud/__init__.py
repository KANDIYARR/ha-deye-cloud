"""Deye Cloud integration for Home Assistant."""

from __future__ import annotations

import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DeyeCloudApi, DeyeCloudApiError
from .const import CONF_EMAIL, CONF_REGION, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS, REGIONS

_LOGGER = logging.getLogger(__name__)


class DeyeCloudCoordinator(DataUpdateCoordinator[dict]):
    """Coordinate and share cached station/device data."""

    def __init__(self, hass: HomeAssistant, api: DeyeCloudApi, station_id: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Deye Cloud HA {station_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
            always_update=False,
        )
        self.api = api
        self.station_id = station_id
        self._devices: list[dict] | None = None
        self._last_inventory = None
        self._last_alerts = 0.0
        self._alerts: dict[str, list[dict]] = {}
        self._alerts_supported = True

    async def _async_update_data(self) -> dict:
        try:
            now = time.monotonic()
            if self._devices is None or self._last_inventory is None or now - self._last_inventory >= 3600:
                self._devices = await self.api.list_station_devices(self.station_id)
                self._last_inventory = now
            serials = [str(d.get("deviceSn")) for d in self._devices if d.get("deviceSn")]
            batches = [serials[i:i + 10] for i in range(0, len(serials), 10)]
            # Requests are deliberately serialized and evenly spaced by the API client.
            device_data: dict[str, dict] = {}
            for batch in batches:
                for device in await self.api.latest_devices(batch):
                    sn = str(device.get("deviceSn", ""))
                    points = device.get("dataList", []) or []
                    values = {}
                    for point in points:
                        key = point.get("key")
                        if key is not None:
                            values[str(key)] = {"value": point.get("value"), "unit": point.get("unit")}
                    device_data[sn] = {**device, "measurements": values}
            station = await self.api.station_latest(self.station_id)
            if self._alerts_supported and now - self._last_alerts >= 300:
                end = int(time.time())
                start = end - 24 * 60 * 60
                alerts: dict[str, list[dict]] = {}
                for serial in serials:
                    try:
                        alerts[serial] = await self.api.device_alerts(serial, start, end)
                    except DeyeCloudApiError as err:
                        if err.status_code == 404:
                            self._alerts_supported = False
                            self._alerts = {}
                            _LOGGER.warning(
                                "Deye Cloud does not provide the device-alert endpoint in this region; alert sensors will be unavailable"
                            )
                            break
                        _LOGGER.warning(
                            "Could not retrieve recent Deye device alerts for %s: %s",
                            serial,
                            err,
                        )
                        continue
                else:
                    self._alerts = alerts
                self._last_alerts = now
            return {"devices": self._devices, "device_data": device_data, "station": station, "alerts": self._alerts}
        except DeyeCloudApiError as err:
            raise UpdateFailed(str(err)) from err


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from configuration.yaml (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured Deye Cloud HA account."""
    # Entries created by earlier builds may only contain the selected region.
    # Resolve and persist the corresponding API URL before creating the client.
    base_url = entry.data.get("base_url")
    if not base_url:
        region = entry.data.get(CONF_REGION)
        base_url = REGIONS.get(region)
        if base_url is None:
            account_email = str(entry.data.get(CONF_EMAIL, "")).casefold()
            candidate_urls = set()
            for sibling in hass.config_entries.async_entries(DOMAIN):
                if sibling.entry_id == entry.entry_id:
                    continue
                sibling_email = str(sibling.data.get(CONF_EMAIL, "")).casefold()
                if account_email and sibling_email and account_email != sibling_email:
                    continue
                sibling_url = sibling.data.get("base_url") or REGIONS.get(
                    sibling.data.get(CONF_REGION)
                )
                if sibling_url:
                    candidate_urls.add(sibling_url.rstrip("/"))
            if len(candidate_urls) == 1:
                base_url = candidate_urls.pop()
        if base_url is None:
            raise ConfigEntryNotReady(
                "The saved Deye Cloud region is missing or unsupported. Remove and re-add this entry to select its region."
            )
        region = next(
            (name for name, url in REGIONS.items() if url.rstrip("/") == base_url.rstrip("/")),
            region,
        )
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_REGION: region, "base_url": base_url},
        )

    api = DeyeCloudApi(
        hass,
        base_url,
        entry.data["app_id"],
        entry.data["app_secret"],
        entry.data["email"],
        entry.data["password"],
    )
    coordinator = DeyeCloudCoordinator(hass, api, int(entry.data["station_id"]))
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.async_close()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
