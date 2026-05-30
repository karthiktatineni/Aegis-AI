from dataclasses import dataclass

from fastapi import Header


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None = None
    roles: tuple[str, ...] = ("owner",)


async def get_current_user(
    x_user_id: str | None = Header(default=None),
    x_user_email: str | None = Header(default=None),
) -> CurrentUser:
    """Authentication-ready dependency.

    Local development runs as a default owner. Production can replace this with
    JWT/session validation without changing route signatures.
    """
    return CurrentUser(id=x_user_id or "local-user", email=x_user_email)
