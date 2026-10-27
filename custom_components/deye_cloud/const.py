"""Constants for the Deye Cloud HA integration."""

from datetime import timedelta

DOMAIN = "deye_cloud"
PLATFORMS = ["sensor", "binary_sensor"]
DEFAULT_SCAN_INTERVAL = timedelta(minutes=2)
INVENTORY_INTERVAL = timedelta(hours=1)
API_TIMEOUT = 30
MAX_DEVICES_PER_REQUEST = 10

CONF_REGION = "region"
CONF_APP_ID = "app_id"
CONF_APP_SECRET = "app_secret"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"

REGIONS = {
    "India": "https://india-developer.deyecloud.com",
    "Europe": "https://eu1-developer.deyecloud.com",
    "Americas": "https://us1-developer.deyecloud.com",
    "Asia Pacific": "https://apc1-developer.deyecloud.com",
}

ATTRIBUTION = "Data provided by Deye Cloud OpenAPI"
