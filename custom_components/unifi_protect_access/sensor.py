from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UniFiUserManagerConfigEntry
from .entity import UniFiConsoleEntity, UniFiUserEntity
from .helpers import setup_dynamic_user_entities


async def async_setup_entry(hass, entry: UniFiUserManagerConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([
        UniFiActiveUsersSensor(entry, coordinator),
        UniFiDeactivatedUsersSensor(entry, coordinator),
    ])
    setup_dynamic_user_entities(
        entry,
        async_add_entities,
        lambda user_id: UniFiUserStatusSensor(entry, coordinator, user_id),
    )


class UniFiUserStatusSensor(UniFiUserEntity, SensorEntity):
    _attr_name = "Account status"
    _attr_icon = "mdi:account-details"

    def __init__(self, entry, coordinator, user_id: str) -> None:
        super().__init__(entry, coordinator, user_id)
        self._attr_unique_id = f"{entry.unique_id}_{user_id}_account_status"

    @property
    def native_value(self) -> str:
        return self.user.status if self.user and self.user.status else "UNKNOWN"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        user = self.user
        if user is None:
            return {}
        return {
            "username": user.username,
            "email": user.email,
            "protect_user_id": user.protect_user_id,
            "ucore_user_id": user.ucore_user_id,
            "owner": user.is_owner,
            "integration_account": user.is_auth_user,
            "manageable": user.manageable,
        }


class UniFiActiveUsersSensor(UniFiConsoleEntity, SensorEntity):
    _attr_name = "Active users"
    _attr_icon = "mdi:account-multiple-check"
    _attr_native_unit_of_measurement = "users"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.unique_id}_active_users"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.active_count


class UniFiDeactivatedUsersSensor(UniFiConsoleEntity, SensorEntity):
    _attr_name = "Deactivated users"
    _attr_icon = "mdi:account-multiple-minus"
    _attr_native_unit_of_measurement = "users"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.unique_id}_deactivated_users"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.deactivated_count
