from __future__ import annotations

from datetime import timedelta

DOMAIN = "unifi_protect_access"
PLATFORMS = ["switch", "sensor", "binary_sensor", "button"]

CONF_API_KEY = "api_key"
CONF_POLL_INTERVAL = "poll_interval"
CONF_EXPOSED_USERS = "exposed_users"

DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False
DEFAULT_POLL_INTERVAL = 30
MIN_POLL_INTERVAL = 15
MAX_POLL_INTERVAL = 300
PRIVATE_METADATA_REFRESH_SECONDS = 600

USERS_API_PATH = "/proxy/users/api/v2"


def update_interval(seconds: int) -> timedelta:
    return timedelta(seconds=max(MIN_POLL_INTERVAL, min(MAX_POLL_INTERVAL, seconds)))
