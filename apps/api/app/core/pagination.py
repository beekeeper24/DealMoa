from dataclasses import dataclass


@dataclass(frozen=True)
class CursorPage[T]:
    items: list[T]
    next_cursor: str | None
