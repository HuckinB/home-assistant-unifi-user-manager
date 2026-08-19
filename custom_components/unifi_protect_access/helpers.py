from __future__ import annotations

from collections.abc import Callable

from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UniFiUserManagerConfigEntry
from .const import CONF_EXPOSED_USERS


def exposed_user_ids(entry: UniFiUserManagerConfigEntry) -> set[str] | None:
    configured = entry.options.get(CONF_EXPOSED_USERS)
    if not configured:
        return None
    return {str(user_id) for user_id in configured}


def setup_dynamic_user_entities(
    entry: UniFiUserManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
    entity_factory: Callable[[str], object | None],
) -> None:
    coordinator = entry.runtime_data.coordinator
    known: set[str] = set()

    def add_new() -> None:
        if coordinator.data is None:
            return
        selected = exposed_user_ids(entry)
        entities = []
        for user_id in coordinator.data.users:
            if user_id in known:
                continue
            if selected is not None and user_id not in selected:
                continue
            entity = entity_factory(user_id)
            if entity is None:
                continue
            known.add(user_id)
            entities.append(entity)
        if entities:
            async_add_entities(entities)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))
