# Deye Cloud for Home Assistant

Monitor Deye hybrid inverters, batteries, and solar stations in Home Assistant using the official Deye Cloud OpenAPI.

**Author:** Vinoth Sakthivel · [vinoth@kandiyar.com](mailto:vinoth@kandiyar.com)

## Features

- Discovers stations and their connected devices from your Deye Cloud account.
- Creates sensors for station-level solar generation, consumption, grid exchange, battery power, battery state of charge, and irradiance when those values are available.
- Dynamically exposes the telemetry keys returned for each device, including model-specific inverter and battery measurements.
- Reports device connectivity, recent Deye alerts, and whether cloud telemetry is fresh.
- Provides a grid-availability indicator when live grid-voltage measurements are available.
- Supports the India, Europe, Americas, and Asia Pacific Deye Cloud regions.

The available measurements vary by inverter, battery/BMS, logger, and firmware. Grid availability is reported as unknown when the API provides no usable grid-voltage values. Because this integration uses cloud telemetry, it is not a substitute for local protection or safety equipment.

## Installation

### HACS custom repository

1. In Home Assistant, open **HACS → Integrations**.
2. Open the menu in the upper-right corner and choose **Custom repositories**.
3. Add this repository URL and select **Integration** as the category.
4. Find **Deye Cloud** in HACS and install it.
5. Restart Home Assistant.

Once this project is published, the repository URL will be:

```text
https://github.com/KANDIYARR/ha-deye-cloud
```

### Manual installation

Copy the `custom_components/deye_cloud` directory into the `custom_components` directory of your Home Assistant configuration, then restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Deye Cloud**.
3. Select the region where your Deye Cloud account is hosted.
4. Enter your Deye developer Application ID and Application Secret, plus your Deye Cloud account email and password.
5. Select the station to add.

Create an application in the [Deye Developer Portal](https://developer.deyecloud.com/app) to obtain the Application ID and secret. Choose the same region as your Deye Cloud account. Credentials are stored in Home Assistant's config entry. The account password is SHA-256 hashed before it is sent to Deye for authentication.

## Data and polling

The integration polls live data every two minutes, refreshes the device inventory hourly, and checks recent device alerts every five minutes. It batches up to 10 device serial numbers per latest-data request, serializes and spaces requests, caches the authentication token, and backs off after transient errors and rate limits. These defaults follow Deye's [API usage best practices](https://developer.deyecloud.com/best-practices).

## Troubleshooting

- **Authentication or station discovery fails:** confirm the application credentials, account email/password, and selected region.
- **Some sensors are missing:** Deye only returns measurements supported by the connected device and its current telemetry. Sensor availability can differ across models and firmware.
- **Grid status is unknown:** the station or inverter telemetry does not currently include a usable grid-voltage measurement.
- **Telemetry appears stale:** check the logger's connection to Deye Cloud and the device's last-upload time.

## References

- [Deye OpenAPI](https://developer.deyecloud.com/api)
- [API usage best practices](https://developer.deyecloud.com/best-practices)
- [India API reference](https://india-developer.deyecloud.com/v2/api-docs)

## License

MIT. See [LICENSE](LICENSE).
