from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from uiprotect.exceptions import ClientError, NotAuthorized

from .api import UniFiUserManagerApi
from .const import CONF_API_KEY, CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, PLATFORMS
from .coordinator import UniFiUserManagerCoordinator


@dataclass(slots=True)
class UniFiUserManagerRuntimeData:
    api: UniFiUserManagerApi
    coordinator: UniFiUserManagerCoordinator


UniFiUserManagerConfigEntry = ConfigEntry[UniFiUserManagerRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: UniFiUserManagerConfigEntry) -> bool:
    if CONF_API_KEY not in entry.data:
        raise ConfigEntryAuthFailed(
            "This version requires a UniFi Protect API key. Reauthenticate the integration."
        )

    api = UniFiUserManagerApi(
        hass,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        api_key=entry.data[CONF_API_KEY],
        verify_ssl=entry.data[CONF_VERIFY_SSL],
    )
    coordinator = UniFiUserManagerCoordinator(
        hass,
        entry,
        api,
        poll_interval=int(entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except NotAuthorized as err:
        await api.async_close()
        raise ConfigEntryAuthFailed from err
    except ClientError as err:
        await api.async_close()
        raise ConfigEntryNotReady from err

    entry.runtime_data = UniFiUserManagerRuntimeData(api=api, coordinator=coordinator)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: UniFiUserManagerConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: UniFiUserManagerConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.api.async_close()
    return unload_ok


async def async_migrate_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Migrate v0.2.x config entries to the UniFi User Manager schema."""
    if entry.version < 3:
        hass.config_entries.async_update_entry(entry, version=3)
    return True
