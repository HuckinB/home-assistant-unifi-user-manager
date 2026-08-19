from __future__ import annotations

from typing import Any, Mapping

import voluptuous as vol
from uiprotect.exceptions import ClientError, NotAuthorized

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import UniFiUserManagerApi
from .const import (
    CONF_API_KEY,
    CONF_EXPOSED_USERS,
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    MAX_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
)


class UniFiUserManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 3

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return UniFiUserManagerOptionsFlow(config_entry)

    async def _validate(self, data: dict[str, Any]):
        api = UniFiUserManagerApi(
            self.hass,
            host=data[CONF_HOST],
            port=int(data[CONF_PORT]),
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            api_key=data[CONF_API_KEY],
            verify_ssl=data[CONF_VERIFY_SSL],
        )
        try:
            return await api.async_get_snapshot()
        finally:
            await api.async_close()

    def _schema(self, defaults: Mapping[str, Any] | None = None) -> vol.Schema:
        defaults = defaults or {}
        return vol.Schema({
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)): selector.TextSelector(),
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=65535, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, vol.UNDEFINED)): selector.TextSelector(),
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, vol.UNDEFINED)): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
            vol.Required(CONF_API_KEY, default=defaults.get(CONF_API_KEY, vol.UNDEFINED)): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
            vol.Required(CONF_VERIFY_SSL, default=defaults.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)): selector.BooleanSelector(),
        })

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                snapshot = await self._validate(user_input)
            except NotAuthorized:
                errors["base"] = "invalid_auth"
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(snapshot.nvr_mac)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=snapshot.nvr_name, data=user_input)
        return self.async_show_form(step_id="user", data_schema=self._schema(), errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, **user_input}
            try:
                snapshot = await self._validate(data)
            except NotAuthorized:
                errors["base"] = "invalid_auth"
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(snapshot.nvr_mac)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(entry, data_updates=data)

        schema = vol.Schema({
            vol.Required(CONF_USERNAME, default=entry.data.get(CONF_USERNAME, "")): selector.TextSelector(),
            vol.Required(CONF_PASSWORD): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
            vol.Required(CONF_API_KEY): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        })
        return self.async_show_form(step_id="reauth_confirm", data_schema=schema, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                snapshot = await self._validate(user_input)
            except NotAuthorized:
                errors["base"] = "invalid_auth"
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(snapshot.nvr_mac)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
        return self.async_show_form(step_id="reconfigure", data_schema=self._schema(entry.data), errors=errors)


class UniFiUserManagerOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        users = []
        runtime = getattr(self.config_entry, "runtime_data", None)
        coordinator = getattr(runtime, "coordinator", None)
        if coordinator is not None and coordinator.data is not None:
            users = [
                selector.SelectOptionDict(value=user_id, label=user.name)
                for user_id, user in sorted(coordinator.data.users.items(), key=lambda item: item[1].name.lower())
            ]

        schema_dict = {
            vol.Required(
                CONF_POLL_INTERVAL,
                default=self.config_entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
            ): selector.NumberSelector(selector.NumberSelectorConfig(
                min=MIN_POLL_INTERVAL,
                max=MAX_POLL_INTERVAL,
                step=5,
                mode=selector.NumberSelectorMode.SLIDER,
                unit_of_measurement="seconds",
            )),
        }
        if users:
            schema_dict[
                vol.Optional(
                    CONF_EXPOSED_USERS,
                    default=self.config_entry.options.get(CONF_EXPOSED_USERS, []),
                )
            ] = selector.SelectSelector(selector.SelectSelectorConfig(
                options=users,
                multiple=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            ))

        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema_dict))
