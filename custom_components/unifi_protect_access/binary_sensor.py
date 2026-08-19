from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UniFiUserManagerConfigEntry
from .entity import UniFiUserEntity
from .helpers import setup_dynamic_user_entities


async def async_setup_entry(hass, entry: UniFiUserManagerConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data.coordinator
    setup_dynamic_user_entities(
        entry,
        async_add_entities,
        lambda user_id: UniFiProtectLinkedBinarySensor(entry, coordinator, user_id),
    )


class UniFiProtectLinkedBinarySensor(UniFiUserEntity, BinarySensorEntity):
    _attr_name = "Protect linked"
    _attr_icon = "mdi:cctv"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, coordinator, user_id: str) -> None:
        super().__init__(entry, coordinator, user_id)
        self._attr_unique_id = f"{entry.unique_id}_{user_id}_protect_linked"

    @property
    def is_on(self) -> bool:
        return bool(self.user and self.user.protect_linked)
