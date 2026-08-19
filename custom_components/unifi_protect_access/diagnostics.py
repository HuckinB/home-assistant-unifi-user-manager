from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import UniFiUserManagerConfigEntry
from .const import CONF_API_KEY

TO_REDACT = {CONF_PASSWORD, CONF_API_KEY, CONF_USERNAME}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: UniFiUserManagerConfigEntry,
) -> dict[str, Any]:
    snapshot = entry.runtime_data.coordinator.data
    users = {}
    if snapshot is not None:
        for user_id, user in snapshot.users.items():
            users[user_id] = {
                "name": "**REDACTED**",
                "email": "**REDACTED**",
                "username": "**REDACTED**",
                "status": user.status,
                "owner": user.is_owner,
                "integration_account": user.is_auth_user,
                "manageable": user.manageable,
                "protect_linked": user.protect_linked,
                "has_ucore_user_id": user.ucore_user_id is not None,
            }
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "last_update_success": entry.runtime_data.coordinator.last_update_success,
        "users": users,
    }
