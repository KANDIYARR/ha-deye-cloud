"""Config flow for Deye Cloud HA."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .api import DeyeCloudApi, DeyeCloudApiError
from .const import CONF_APP_ID, CONF_APP_SECRET, CONF_EMAIL, CONF_PASSWORD, CONF_REGION, CONF_STATION_ID, CONF_STATION_NAME, DOMAIN, REGIONS


class DeyeCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure Deye Cloud HA credentials and select a plant."""

    VERSION = 1

    def __init__(self) -> None:
        self._credentials: dict = {}
        self._stations: list[dict] = []
        self._api: DeyeCloudApi | None = None

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            region = user_input[CONF_REGION]
            api = DeyeCloudApi(
                self.hass,
                REGIONS[region],
                user_input[CONF_APP_ID],
                user_input[CONF_APP_SECRET],
                user_input[CONF_EMAIL],
                user_input[CONF_PASSWORD],
            )
            try:
                stations = await api.list_stations()
            except DeyeCloudApiError:
                errors["base"] = "cannot_connect"
                await api.async_close()
            else:
                if not stations:
                    await api.async_close()
                    errors["base"] = "no_stations"
                else:
                    self._credentials = {**user_input, "base_url": REGIONS[region]}
                    self._stations = stations
                    self._api = api
                    return await self.async_step_station()
        schema = vol.Schema({
            vol.Required(CONF_REGION, default="India"): vol.In(list(REGIONS)),
            vol.Required(CONF_APP_ID): str,
            vol.Required(CONF_APP_SECRET): str,
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_station(self, user_input=None):
        if user_input:
            station_id = str(user_input[CONF_STATION_ID])
            station = next(s for s in self._stations if str(s.get("id", s.get("stationId"))) == station_id)
            await self._api.async_close()
            await self.async_set_unique_id(f"{self._credentials[CONF_EMAIL]}_{station_id}".lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=str(station.get("name") or station.get("stationName") or f"Deye station {station_id}"),
                data={**self._credentials, CONF_STATION_ID: station_id, CONF_STATION_NAME: station.get("name", "Deye station")},
            )
        options = {
            str(s.get("id", s.get("stationId"))): str(s.get("name") or s.get("stationName") or s.get("id"))
            for s in self._stations
            if s.get("id", s.get("stationId")) is not None
        }
        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema({vol.Required(CONF_STATION_ID): vol.In(options)}),
        )
