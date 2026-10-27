"""Station and device telemetry sensors."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "measurement"


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class Metric:
    key: str
    name: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT


STATION_METRICS = (
    Metric("generationPower", "Generation power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    Metric("consumptionPower", "Consumption power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    Metric("gridPower", "Grid power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    Metric("purchasePower", "Grid import power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    Metric("wirePower", "Grid export power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    Metric("batteryPower", "Battery power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    Metric("chargePower", "Battery charge power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    Metric("dischargePower", "Battery discharge power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    Metric("batterySOC", "Battery state of charge", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
    Metric("irradiateIntensity", "Solar irradiance", "W/m²"),
)


def _metric_metadata(key: str, unit: str | None) -> tuple[str | None, str | None, str | None]:
    normalized = key.lower()
    unit_norm = (unit or "").lower()
    if unit_norm in {"w", "kw"} or "power" in normalized:
        return UnitOfPower.WATT if unit_norm != "kw" else "kW", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT
    if unit_norm in {"kwh", "wh"}:
        return UnitOfEnergy.KILO_WATT_HOUR if unit_norm != "wh" else UnitOfEnergy.WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING
    if unit_norm in {"%", "percent"} or "soc" in normalized:
        return PERCENTAGE, SensorDeviceClass.BATTERY if "soc" in normalized else None, SensorStateClass.MEASUREMENT
    if unit_norm in {"v", "volt", "volts"}:
        return "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT
    if unit_norm in {"a", "amp", "amps"}:
        return "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT
    if unit_norm in {"hz"}:
        return "Hz", SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT
    if unit_norm in {"°c", "c", "℃"}:
        return "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT
    if unit_norm == "kwh":
        return UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING
    return unit, None, SensorStateClass.MEASUREMENT


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for metric in STATION_METRICS:
        entities.append(DeyeStationSensor(coordinator, entry, metric))
    entities.extend([DeyeStationTimeSensor(coordinator, entry)])
    seen: set[tuple[str, str]] = set()
    for device in coordinator.data.get("devices", []):
        sn = str(device.get("deviceSn", ""))
        if sn:
            entities.append(DeyeDeviceStateSensor(coordinator, entry, sn, device))
    for sn, info in coordinator.data.get("device_data", {}).items():
        for key, reading in info["measurements"].items():
            identity = (sn, key)
            if identity in seen:
                continue
            seen.add(identity)
            entities.append(DeyeMeasurementSensor(coordinator, entry, sn, key, reading))
    async_add_entities(entities)


class DeyeStationSensor(CoordinatorEntity, SensorEntity):
    """A station-level aggregate value."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, entry, metric: Metric) -> None:
        super().__init__(coordinator)
        self._metric = metric
        self._attr_name = f"{entry.title} {metric.name}"
        self._attr_unique_id = f"{entry.entry_id}_station_{metric.key}"
        self._attr_native_unit_of_measurement = metric.unit
        self._attr_device_class = metric.device_class
        self._attr_state_class = metric.state_class
        self._attr_suggested_display_precision = 1
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name=entry.title, manufacturer="Deye", model="Cloud station")

    @property
    def native_value(self):
        value = _number(self.coordinator.data.get("station", {}).get(self._metric.key))
        return value


class DeyeStationTimeSensor(CoordinatorEntity, SensorEntity):
    """Time Deye last updated station telemetry."""

    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} Last update"
        self._attr_unique_id = f"{entry.entry_id}_station_last_update"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name=entry.title, manufacturer="Deye", model="Cloud station")

    @property
    def native_value(self):
        from datetime import datetime
        from homeassistant.util import dt as dt_util
        value = self.coordinator.data.get("station", {}).get("lastUpdateTime")
        if not value:
            return None
        try:
            parsed = dt_util.parse_datetime(str(value))
            if parsed:
                return parsed
            return datetime.fromtimestamp(float(value), tz=dt_util.UTC)
        except (ValueError, TypeError, OSError):
            return None


class DeyeDeviceStateSensor(CoordinatorEntity, SensorEntity):
    """Raw device state code."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, entry, serial: str, device: dict) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_name = f"{entry.title} {serial} Device state"
        self._attr_unique_id = f"{entry.entry_id}_{serial}_device_state"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Deye {device.get('deviceType', 'device')} {serial}", manufacturer="Deye", model=device.get("deviceType"), via_device=(DOMAIN, entry.entry_id))

    @property
    def native_value(self):
        info = self.coordinator.data.get("device_data", {}).get(self._serial, {})
        return info.get("deviceState")


class DeyeMeasurementSensor(CoordinatorEntity, SensorEntity):
    """A raw Deye device measurement, retained with the API key as a suffix."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, entry, serial: str, key: str, initial: dict) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._key = key
        self._unit, device_class, state_class = _metric_metadata(key, initial.get("unit"))
        self._attr_name = f"{serial} {_slug(key)}"
        self._attr_unique_id = f"{entry.entry_id}_{serial}_{_slug(key)}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = self._unit
        self._attr_suggested_display_precision = 2
        self._attr_extra_state_attributes = {"deye_measurement_key": key, "device_serial": serial}
        if self._unit is None:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, serial)}, name=f"Deye device {serial}", manufacturer="Deye", via_device=(DOMAIN, entry.entry_id))

    @property
    def native_value(self):
        info = self.coordinator.data.get("device_data", {}).get(self._serial, {})
        reading = info.get("measurements", {}).get(self._key, {})
        return _number(reading.get("value"))
