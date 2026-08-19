from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class UniFiUserState:
    protect_user_id: str
    ucore_user_id: str | None
    name: str
    username: str
    email: str | None
    is_owner: bool
    is_auth_user: bool
    status: str | None
    protect_linked: bool

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    @property
    def manageable(self) -> bool:
        return (
            not self.is_owner
            and not self.is_auth_user
            and self.ucore_user_id is not None
            and self.status in {"ACTIVE", "DEACTIVATED"}
        )


@dataclass(slots=True, frozen=True)
class UniFiUserSnapshot:
    nvr_id: str
    nvr_name: str
    nvr_mac: str
    auth_user_id: str
    users: dict[str, UniFiUserState]

    @property
    def active_count(self) -> int:
        return sum(user.status == "ACTIVE" for user in self.users.values())

    @property
    def deactivated_count(self) -> int:
        return sum(user.status == "DEACTIVATED" for user in self.users.values())
