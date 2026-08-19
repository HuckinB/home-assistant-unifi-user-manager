from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import UniFiUserManagerConfigEntry
from .const import DOMAIN
from .coordinator import UniFiUserManagerCoordinator
from .models import UniFiUserState


class UniFiUserEntity(CoordinatorEntity[UniFiUserManagerCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: UniFiUserManagerConfigEntry,
        coordinator: UniFiUserManagerCoordinator,
        user_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._user_id = user_id
        user = coordinator.data.users[user_id]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}:user:{user_id}")},
            manufacturer="Ubiquiti",
            model="UniFi User",
            name=user.name,
            configuration_url=f"https://{entry.data[CONF_HOST]}",
            via_device=(DOMAIN, f"{entry.unique_id}:console"),
        )

    @property
    def user(self) -> UniFiUserState | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.users.get(self._user_id)


class UniFiConsoleEntity(CoordinatorEntity[UniFiUserManagerCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: UniFiUserManagerConfigEntry,
        coordinator: UniFiUserManagerCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        snapshot = coordinator.data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}:console")},
            manufacturer="Ubiquiti",
            model="UniFi Console",
            name=snapshot.nvr_name,
            configuration_url=f"https://{entry.data[CONF_HOST]}",
        )
