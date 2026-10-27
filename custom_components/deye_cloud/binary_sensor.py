"""Grid and device status binary sensors."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = [
        DeyeGridAvailable(coordinator, entry),
        DeyeCloudTelemetryFresh(coordinator, entry),
    ]
    for device in coordinator.data.get("devices", []):
        serial = str(device.get("deviceSn", ""))
        if serial:
            entities.append(DeyeDeviceOnline(coordinator, entry, serial, device))
            entities.append(DeyeActiveAlert(coordinator, entry, serial, device))
    async_add_entities(entities)


class DeyeGridAvailable(CoordinatorEntity, BinarySensorEntity):
    """Grid connectivity inferred from latest inverter measurements."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} Grid available"
        self._attr_unique_id = f"{entry.entry_id}_grid_available"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name=entry.title, manufacturer="Deye", model="Cloud station")
        self._entry = entry

    @property
    def is_on(self):
        station = self.coordinator.data.get("station", {})
        grid_keys = ("gridVoltage", "gridVoltageL1", "gridVoltageL2", "gridVoltageL3")
        observed = [station.get(key) for key in grid_keys if station.get(key) is not None]
        for info in self.coordinator.data.get("device_data", {}).values():
            for key, reading in info.get("measurements", {}).items():
                normalized = key.lower().replace(" ", "")
                if "grid" in normalized and ("voltage" in normalized or "vgrid" in normalized):
                    observed.append(reading.get("value"))
        if not observed:
            return None
        try:
            # Any live phase voltage indicates grid presence. On single phase and three phase devices alike.
            return any(float(value) > 80 for value in observed if value is not None)
        except (TypeError, ValueError):
            return None


class DeyeCloudTelemetryFresh(CoordinatorEntity, BinarySensorEntity):
    """Cloud telemetry freshness, which helps diagnose lost logger updates."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_attribution = ATTRIBUTION
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} Telemetry fresh"
        self._attr_unique_id = f"{entry.entry_id}_telemetry_fresh"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name=entry.title, manufacturer="Deye", model="Cloud station")

    @property
    def is_on(self):
        from datetime import datetime, timezone
        value = self.coordinator.data.get("station", {}).get("lastUpdateTime")
        if value is None:
            return None
        try:
            timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
        except ValueError:
            try:
                timestamp = float(value)
            except (TypeError, ValueError):
                return None
        return datetime.now(timezone.utc).timestamp() - timestamp < timedelta(minutes=10).total_seconds()


class DeyeDeviceOnline(CoordinatorEntity, BinarySensorEntity):
    """Cloud connectivity status for a Deye device."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, entry, serial: str, device: dict) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = f"{serial} Online"
        self._attr_unique_id = f"{entry.entry_id}_{serial}_online"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Deye {device.get('deviceType', 'device')} {serial}", manufacturer="Deye", model=device.get("deviceType"), via_device=(DOMAIN, entry.entry_id))

    @property
    def is_on(self):
        info = self.coordinator.data.get("device_data", {}).get(self._serial)
        if info is None:
            return False
        state = info.get("deviceState")
        if state is None:
            state = next((d.get("connectStatus") for d in self.coordinator.data.get("devices", []) if str(d.get("deviceSn")) == self._serial), None)
        if state is None:
            return None
        return str(state) in {"1", "ONLINE", "online"}


class DeyeActiveAlert(CoordinatorEntity, BinarySensorEntity):
    """Indicate an alert that has not been cleared in the recent alert window."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, entry, serial: str, device: dict) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = f"{serial} Active alert"
        self._attr_unique_id = f"{entry.entry_id}_{serial}_active_alert"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Deye {device.get('deviceType', 'device')} {serial}", manufacturer="Deye", model=device.get("deviceType"), via_device=(DOMAIN, entry.entry_id))

    @property
    def is_on(self):
        alerts = self.coordinator.data.get("alerts", {}).get(self._serial)
        if alerts is None:
            return None
        return any(str(alert.get("status", "")) not in {"0", "CLOSED", "closed", "resolved"} for alert in alerts)

    @property
    def extra_state_attributes(self):
        alerts = self.coordinator.data.get("alerts", {}).get(self._serial) or []
        return {
            "alerts": [
                {k: alert.get(k) for k in ("alertName", "description", "reason", "solution", "level", "status", "alertStartTime", "alertEndTime") if alert.get(k) is not None}
                for alert in alerts[:20]
            ]
        }
