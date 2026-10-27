<div align="center">

# Deye Cloud

**Deye hybrid inverters and batteries, connected to Home Assistant.**

Cloud telemetry · Grid status · HACS custom repository

[![HACS custom repository](https://img.shields.io/badge/HACS-Custom_repository-41BDF5)](#installation)
[![License: MIT](https://img.shields.io/badge/Code_license-MIT-222222)](LICENSE)

[Install](#installation) · [Features](#features) · [Compatibility](#compatibility) · [Report an issue](https://github.com/KANDIYARR/ha-deye-cloud/issues)

</div>

---

Monitor a Deye Cloud solar station in Home Assistant. Sign in with your Deye
developer application and Deye Cloud account, choose a station, and the
integration discovers its inverters, batteries, and other supported devices.

## Features

| Entity | Data |
| :--- | :--- |
| **Station** | Solar generation, consumption, grid exchange, battery power and state of charge, irradiance, and last cloud update when provided |
| **Inverter and battery devices** | Dynamically created sensors for the telemetry keys returned by each device, with reported units where available |
| **Grid availability** | Estimates grid presence from live grid-voltage measurements; reports unknown when voltage data is unavailable |
| **Device connectivity** | Online status, device state, and recent alerts |
| **Cloud telemetry** | Freshness indicator based on the station's last update timestamp |

- **Cloud API:** uses Deye Cloud OpenAPI; it does not communicate with the inverter over a local network.
- **Broad telemetry coverage:** exposes data keys returned by each device, including model-specific measurements. Available values depend on the inverter, battery/BMS, logger, firmware, and Deye's API response.
- **Conservative request pacing:** caches the authentication token, spaces API requests, batches latest-data requests, and retries transient errors with backoff, following Deye's [API usage best practices](https://developer.deyecloud.com/best-practices).

Grid availability is inferred from measured voltage and may not immediately reflect a power cut. Cloud updates can be delayed, and the indicator is unknown if usable voltage is not reported. This integration is for monitoring and must not be used as a safety or protection system.

## Installation

### Through HACS

**1 · Add the repository**

Open **HACS → ⋮ → Custom repositories**, paste the URL below, choose
**Integration**, and select **Add**.

```text
https://github.com/KANDIYARR/ha-deye-cloud
```

**2 · Download and restart**

Find **Deye Cloud** in HACS, download it, then restart Home Assistant.

**3 · Connect your station**

Go to **Settings → Devices & services → Add integration → Deye Cloud**.
Choose your Deye Cloud region, enter your Deye developer Application ID and
Application Secret along with your Deye Cloud email and password, then select
the station to add.

Create an application in the [Deye Developer Portal](https://developer.deyecloud.com/app).
Choose the region matching your Deye Cloud account.

[View the HACS custom repository guide →](https://www.hacs.dev/docs/faq/custom_repositories/)

<details>
<summary><strong>Prefer a manual installation?</strong></summary>

1. Download or clone this repository.
2. Copy `custom_components/deye_cloud` into your Home Assistant configuration's `custom_components` directory.
3. Restart Home Assistant.
4. Add **Deye Cloud** under **Settings → Devices & services** and configure your account.

Your configuration should contain:

```text
config/
└── custom_components/
    └── deye_cloud/
        ├── __init__.py
        ├── api.py
        ├── manifest.json
        └── …
```

</details>

## Compatibility

| Requirement | Details |
| :--- | :--- |
| **Home Assistant** | A current release with config-flow and coordinator support |
| **Account** | Deye Cloud account and Deye developer application credentials |
| **Region** | India, Europe, Americas, or Asia Pacific |
| **Connection** | Internet access to the selected Deye Cloud API region |
| **Device coverage** | Deye Cloud devices and measurements exposed by the account's API permissions |

Sensor availability and naming can vary by device model, BMS, logger, firmware, and the data returned by Deye Cloud. Unsupported or unreported measurements cannot be created by the integration.

## Data refresh and privacy

Station and device telemetry refreshes every **2 minutes**. Device inventory is refreshed hourly, and recent device alerts are checked every **5 minutes**. Latest-data requests batch up to 10 devices, and requests are serialized and spaced to reduce API load.

The account password is SHA-256 hashed before authentication. Application credentials, account email, and password are stored in the Home Assistant config entry. Protect Home Assistant configuration backups accordingly. Deye Cloud availability and upload delays affect the freshness of the readings.

## Verification

This integration has not yet been validated against a live Deye installation or a running Home Assistant instance. The repository includes the implementation and setup metadata; actual telemetry coverage depends on the responses available from the connected Deye account.

## Everyday use

- Allow for the next scheduled cloud refresh before expecting sensor values to change.
- If devices or sensors are missing, confirm the Deye logger is online and that Deye Cloud reports the measurement for the selected device.
- If grid availability is unknown, check whether the inverter exposes usable grid-voltage telemetry.
- If authentication fails, confirm the application credentials and that the selected region matches your Deye Cloud account.
- Include your Home Assistant version, integration version, device model, and a redacted error when reporting an issue. Never post passwords, application secrets, or tokens.

<details>
<summary><strong>API references</strong></summary>

- [Deye OpenAPI](https://developer.deyecloud.com/api)
- [API usage best practices](https://developer.deyecloud.com/best-practices)
- [India API reference](https://india-developer.deyecloud.com/v2/api-docs)
- [Integration repository](https://github.com/KANDIYARR/ha-deye-cloud)

</details>

## Author & support

**Vinoth Sakthivel** · [@KANDIYARR](https://github.com/KANDIYARR)

[vinoth@kandiyar.com](mailto:vinoth@kandiyar.com) · [Report an issue](https://github.com/KANDIYARR/ha-deye-cloud/issues)

## License & attribution

Integration code is **[MIT licensed](LICENSE)**, copyright © 2026 Vinoth Sakthivel.
The Deye name and trademarks belong to their respective owners. This project is
not affiliated with or endorsed by Deye.
