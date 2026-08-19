from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UniFiUserManagerConfigEntry
from .entity import UniFiConsoleEntity


async def async_setup_entry(hass, entry: UniFiUserManagerConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([UniFiRefreshUsersButton(entry, entry.runtime_data.coordinator)])


class UniFiRefreshUsersButton(UniFiConsoleEntity, ButtonEntity):
    _attr_name = "Refresh users"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.unique_id}_refresh_users"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
