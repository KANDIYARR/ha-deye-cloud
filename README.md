<p align="center">
  <strong>DEYE CLOUD · HOME ASSISTANT</strong>
</p>

<h1 align="center">Deye Cloud</h1>

<p align="center">
  <strong>Your Deye hybrid inverter and battery, connected to Home Assistant.</strong><br>
  Solar telemetry, battery status and grid availability through Deye Cloud.
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=KANDIYARR&amp;repository=ha-deye-cloud&amp;category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Add Deye Cloud to HACS"></a>
  <a href="https://www.hacs.dev/docs/faq/custom_repositories/"><img src="https://img.shields.io/badge/HACS-Custom_repository-41BDF5?style=flat-square" alt="HACS custom repository"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-555?style=flat-square" alt="MIT license"></a>
</p>

<p align="center">
  <a href="#installation">Installation</a> ·
  <a href="#features">Features</a> ·
  <a href="#requirements">Requirements</a> ·
  <a href="#troubleshooting">Troubleshooting</a> ·
  <a href="https://github.com/KANDIYARR/ha-deye-cloud/issues">Report an issue</a>
</p>

---

## Overview

Monitor a Deye Cloud solar station in Home Assistant. Connect with a Deye
developer application and your Deye Cloud account, select a station, and the
integration discovers its inverters, batteries, and other devices visible to
the account.

| Capability | What it provides |
| --- | --- |
| **Station summary** | Solar generation, consumption, grid exchange, battery power and state of charge, irradiance, and last update when returned by the API. |
| **Device telemetry** | Dynamically created sensors for the measurement keys and units returned by each inverter, battery/BMS, or other device. |
| **Grid availability** | Estimates grid presence from live grid-voltage readings and reports unknown when no usable voltage is available. |
| **Device health** | Online status, device state, recent alerts, and cloud telemetry freshness. |
| **API request handling** | Cached authentication token, serialized and spaced requests, batches of up to 10 devices, and retry backoff for transient errors. |

This integration uses Deye Cloud and does not connect directly to the inverter over a local network. Available values depend on device model, BMS, logger, firmware, account permissions, and Deye's API response. Grid status is inferred from cloud voltage telemetry; it may be delayed and is not a safety or protection feature.

## Requirements

- A current Home Assistant release with config-flow and coordinator support.
- A Deye Cloud account with a station and devices already registered.
- A Deye Developer Portal application with its Application ID and secret.
- Internet access to the Deye Cloud API endpoint for your account's region.
- HACS for the recommended installation method.

Supported API regions in this integration: **India, Europe, Americas, and Asia Pacific**. Use the region that hosts your Deye Cloud account.

## Installation

### HACS · Recommended

[![Add Deye Cloud to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KANDIYARR&repository=ha-deye-cloud&category=integration)

Use the button above, or add the repository manually:

1. Open **HACS → ⋮ → Custom repositories**.
2. Add the URL below and choose **Integration**:

   ```text
   https://github.com/KANDIYARR/ha-deye-cloud
   ```

3. Find **Deye Cloud** and download it.
4. **Restart Home Assistant.**
5. Go to **Settings → Devices & services → Add integration → Deye Cloud**.
6. Select your region, enter your Deye application credentials and Deye Cloud account email and password, then choose a station.

Create an application in the [Deye Developer Portal](https://developer.deyecloud.com/app). The selected region must match your Deye Cloud account.

> **Distribution:** This repository is available through HACS as a custom repository. It is not currently listed in the HACS default catalog.

<details>
<summary><strong>Manual installation</strong></summary>

1. Download or clone this repository.
2. Copy `custom_components/deye_cloud` into your Home Assistant configuration:

   ```text
   config/
   └── custom_components/
       └── deye_cloud/
           ├── __init__.py
           ├── api.py
           ├── manifest.json
           └── ...
   ```

3. Restart Home Assistant.
4. Add **Deye Cloud** from **Settings → Devices & services** and configure your account.

</details>

## Data refresh and privacy

Station and device telemetry refreshes every **2 minutes**. Device inventory is refreshed hourly, and recent device alerts are checked every **5 minutes**. Latest-data requests include up to 10 devices and are serialized and spaced to reduce API load. Retry backoff is applied to transient failures and rate limits, following Deye's [API usage best practices](https://developer.deyecloud.com/best-practices).

The account password is SHA-256 hashed before authentication. The application credentials, account email, and password are stored in Home Assistant's config entry. Protect your Home Assistant configuration and backups accordingly. Cloud upload delays can make readings stale.

## Verification status

The integration has not yet been validated against a live Deye installation or a running Home Assistant instance. The repository contains the integration code and setup metadata; actual sensor availability depends on the API data returned for your equipment and account.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| **Authentication or station discovery fails** | Confirm the application credentials, account email/password, application access, and selected region. |
| **No devices or measurements appear** | Confirm the Deye logger is online and that Deye Cloud reports data for the device. Different equipment and firmware expose different measurements. |
| **Grid availability is unknown** | The inverter telemetry may not include a usable grid-voltage measurement. |
| **Telemetry is delayed or stale** | Check the logger's internet connection and the device's last upload time in Deye Cloud. |

For help, [open an issue](https://github.com/KANDIYARR/ha-deye-cloud/issues) with your Home Assistant version, integration version, device model, and a redacted error message. Never include passwords, application secrets, or access tokens.

## Compatibility and limitations

The integration exposes measurements returned by Deye Cloud for the selected station's devices. Sensor sets, keys, units, and availability vary across inverter models, batteries/BMS, loggers, firmware, and API permissions. Measurements not returned by the API cannot be exposed as sensors.

This is a cloud-polling integration. It depends on internet access, Deye Cloud availability, and the logger's upload schedule. Grid availability is an estimate based on reported voltage and may not immediately identify a power failure. Do not use it for electrical protection, backup switching, or other safety-critical decisions.

## API references

- [Deye OpenAPI](https://developer.deyecloud.com/api)
- [Deye API best practices](https://developer.deyecloud.com/best-practices)
- [India API reference](https://india-developer.deyecloud.com/v2/api-docs)

## Author and support

**Vinoth Sakthivel** · [@KANDIYARR](https://github.com/KANDIYARR) · [vinoth@kandiyar.com](mailto:vinoth@kandiyar.com)

[Report an issue](https://github.com/KANDIYARR/ha-deye-cloud/issues)

## License and attribution

Integration code is distributed under the **[MIT License](LICENSE)**, copyright © 2026 Vinoth Sakthivel. Deye names and trademarks belong to their respective owners. This is an independent project and is not affiliated with or endorsed by Deye.
