from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UniFiUserManagerConfigEntry
from .entity import UniFiUserEntity
from .helpers import setup_dynamic_user_entities


async def async_setup_entry(hass, entry: UniFiUserManagerConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data.coordinator

    def factory(user_id: str):
        user = coordinator.data.users[user_id]
        if not user.manageable:
            return None
        return UniFiUserAccountSwitch(entry, coordinator, user_id)

    setup_dynamic_user_entities(entry, async_add_entities, factory)


class UniFiUserAccountSwitch(UniFiUserEntity, SwitchEntity):
    _attr_icon = "mdi:account-check"
    _attr_name = "Account active"

    def __init__(self, entry, coordinator, user_id: str) -> None:
        super().__init__(entry, coordinator, user_id)
        self._attr_unique_id = f"{entry.unique_id}_{user_id}_account_active"

    @property
    def available(self) -> bool:
        return bool(super().available and self.user and self.user.manageable)

    @property
    def is_on(self) -> bool:
        return bool(self.user and self.user.is_active)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        user = self.user
        if user is None:
            return {}
        return {
            "username": user.username,
            "email": user.email,
            "ucore_user_id": user.ucore_user_id,
            "protect_user_id": user.protect_user_id,
            "account_status": user.status,
        }

    async def async_turn_off(self, **kwargs) -> None:
        user = self.user
        if user is None or not user.manageable or user.ucore_user_id is None:
            raise HomeAssistantError("This UniFi user cannot be managed")
        try:
            await self._entry.runtime_data.api.async_deactivate_user(user.ucore_user_id)
        except Exception as err:
            raise HomeAssistantError(f"Failed to deactivate {user.name}: {err}") from err
        self.coordinator.async_set_user_status(self._user_id, "DEACTIVATED")
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        user = self.user
        if user is None or not user.manageable or user.ucore_user_id is None:
            raise HomeAssistantError("This UniFi user cannot be managed")
        try:
            await self._entry.runtime_data.api.async_activate_user(user.ucore_user_id)
        except Exception as err:
            raise HomeAssistantError(f"Failed to activate {user.name}: {err}") from err
        self.coordinator.async_set_user_status(self._user_id, "ACTIVE")
        await self.coordinator.async_request_refresh()
