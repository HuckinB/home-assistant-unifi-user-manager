from __future__ import annotations

import logging
from dataclasses import replace
from time import monotonic

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from uiprotect.exceptions import ClientError, NotAuthorized

from .api import UniFiUserManagerApi
from .const import (
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    PRIVATE_METADATA_REFRESH_SECONDS,
    update_interval,
)
from .models import UniFiUserSnapshot

_LOGGER = logging.getLogger(__name__)


class UniFiUserManagerCoordinator(DataUpdateCoordinator[UniFiUserSnapshot]):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: UniFiUserManagerApi,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=update_interval(poll_interval),
        )
        self.api = api
        self._last_private_refresh = 0.0

    async def _async_update_data(self) -> UniFiUserSnapshot:
        now = monotonic()
        refresh_private = (
            self.data is None
            or now - self._last_private_refresh >= PRIVATE_METADATA_REFRESH_SECONDS
        )
        try:
            snapshot = await self.api.async_get_snapshot(
                previous_snapshot=self.data,
                refresh_private_metadata=refresh_private,
            )
        except NotAuthorized as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ClientError as err:
            raise UpdateFailed(str(err)) from err

        if refresh_private:
            self._last_private_refresh = now
        return snapshot

    def async_set_user_status(self, user_id: str, status: str) -> None:
        if self.data is None:
            return
        user = self.data.users.get(user_id)
        if user is None:
            return
        users = dict(self.data.users)
        users[user_id] = replace(user, status=status)
        self.async_set_updated_data(replace(self.data, users=users))
