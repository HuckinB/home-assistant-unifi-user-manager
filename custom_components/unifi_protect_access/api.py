from __future__ import annotations

from pathlib import Path
from typing import Any

from aiohttp import CookieJar
from uiprotect import ProtectApiClient
from uiprotect.exceptions import NvrError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.storage import STORAGE_DIR

from .const import USERS_API_PATH
from .models import UniFiUserSnapshot, UniFiUserState


class UniFiUserManagerApi:
    def __init__(
        self,
        hass: HomeAssistant,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        api_key: str,
        verify_ssl: bool,
    ) -> None:
        private_session = async_create_clientsession(
            hass,
            verify_ssl=verify_ssl,
            cookie_jar=CookieJar(unsafe=True),
        )
        public_session = async_create_clientsession(hass, verify_ssl=verify_ssl)
        storage_path = Path(hass.config.path(STORAGE_DIR, "unifi_protect_access"))

        self._client = ProtectApiClient(
            host=host,
            port=port,
            username=username,
            password=password,
            api_key=api_key,
            verify_ssl=verify_ssl,
            session=private_session,
            public_api_session=public_session,
            cache_dir=storage_path,
            config_dir=storage_path,
            store_sessions=False,
        )

    async def async_close(self) -> None:
        await self._client.close_session()

    async def _async_public_list(self, url: str) -> list[dict[str, Any]]:
        data = await self._client.api_request(url, public_api=True)
        if not isinstance(data, list):
            raise NvrError(f"Unexpected response from UniFi public API: {url}")
        return [item for item in data if isinstance(item, dict)]

    async def async_get_snapshot(
        self,
        *,
        previous_snapshot: UniFiUserSnapshot | None = None,
        refresh_private_metadata: bool = True,
    ) -> UniFiUserSnapshot:
        bootstrap = (
            await self._client.get_bootstrap()
            if refresh_private_metadata or previous_snapshot is None
            else None
        )
        public_users = await self._async_public_list("/v1/users")
        ulp_users = await self._async_public_list("/v1/ulp-users")

        private_by_id = (
            {user.id: user for user in bootstrap.users.values()}
            if bootstrap is not None
            else {}
        )
        public_by_protect_id = {
            str(user["id"]): user for user in public_users if user.get("id") is not None
        }
        ulp_by_id = {
            str(user["id"]): user for user in ulp_users if user.get("id") is not None
        }

        previous_users = previous_snapshot.users if previous_snapshot is not None else {}
        user_ids = set(private_by_id) | set(public_by_protect_id) | set(previous_users)
        users: dict[str, UniFiUserState] = {}

        for user_id in user_ids:
            private_user = private_by_id.get(user_id)
            public_user = public_by_protect_id.get(user_id, {})
            previous_user = previous_users.get(user_id)

            raw_ucore_user_id = public_user.get("ucoreUserId")
            ucore_user_id = (
                str(raw_ucore_user_id)
                if raw_ucore_user_id is not None
                else previous_user.ucore_user_id
                if previous_user is not None
                else None
            )

            ulp_user = ulp_by_id.get(ucore_user_id, {}) if ucore_user_id else {}
            raw_status = ulp_user.get("status")
            status = (
                str(raw_status).upper()
                if raw_status is not None
                else previous_user.status
                if previous_user is not None
                else None
            )

            if private_user is not None:
                display_name = (
                    private_user.name
                    or " ".join(
                        part
                        for part in (private_user.first_name, private_user.last_name)
                        if part
                    ).strip()
                    or private_user.local_username
                    or private_user.email
                    or user_id
                )
                username = private_user.local_username or ""
                email = private_user.email
                is_owner = private_user.is_owner
            else:
                public_name = public_user.get("name")
                display_name = (
                    str(public_name)
                    if public_name
                    else previous_user.name
                    if previous_user is not None
                    else user_id
                )
                username = previous_user.username if previous_user is not None else ""
                raw_email = public_user.get("email")
                email = (
                    str(raw_email)
                    if raw_email is not None
                    else previous_user.email
                    if previous_user is not None
                    else None
                )
                is_owner = previous_user.is_owner if previous_user is not None else False

            is_auth_user = (
                (bootstrap is not None and user_id == bootstrap.auth_user_id)
                or (previous_user.is_auth_user if previous_user is not None else False)
            )

            users[user_id] = UniFiUserState(
                protect_user_id=user_id,
                ucore_user_id=ucore_user_id,
                name=display_name,
                username=username,
                email=email,
                is_owner=is_owner,
                is_auth_user=is_auth_user,
                status=status,
                protect_linked=user_id in public_by_protect_id or user_id in private_by_id,
            )

        if bootstrap is not None:
            nvr_id = bootstrap.nvr.id
            nvr_name = bootstrap.nvr.display_name
            nvr_mac = bootstrap.nvr.mac
            auth_user_id = bootstrap.auth_user_id
        elif previous_snapshot is not None:
            nvr_id = previous_snapshot.nvr_id
            nvr_name = previous_snapshot.nvr_name
            nvr_mac = previous_snapshot.nvr_mac
            auth_user_id = previous_snapshot.auth_user_id
        else:
            raise NvrError("UniFi console metadata is not available")

        return UniFiUserSnapshot(
            nvr_id=nvr_id,
            nvr_name=nvr_name,
            nvr_mac=nvr_mac,
            auth_user_id=auth_user_id,
            users=users,
        )

    async def async_deactivate_user(self, ucore_user_id: str) -> None:
        await self._client.api_request_raw(
            f"/user/{ucore_user_id}/deactivate?isULP=1",
            method="put",
            api_path=USERS_API_PATH,
        )

    async def async_activate_user(self, ucore_user_id: str) -> None:
        await self._client.api_request_raw(
            f"/user/{ucore_user_id}/active?isULP=1",
            method="put",
            api_path=USERS_API_PATH,
        )
