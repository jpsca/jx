"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
import logging
import typing as t
import uuid
from collections import UserString

from markupsafe import Markup


logger = logging.getLogger("jx")


class CallerWrapper(UserString):
    def __init__(self, caller: t.Callable | None, content: str | None = None) -> None:
        self._caller = caller
        self._content = Markup(content or "")

    def __call__(self, slot: str = "") -> str:
        if slot and self._caller:
            return self._caller(slot)
        return self.data

    def __html__(self) -> str:
        return self.__call__()

    def __repr__(self) -> str:
        return self.data

    def __str__(self) -> str:
        return self.data

    @property
    def data(self) -> str:  # type: ignore
        return self._caller("") if self._caller else self._content


def get_random_id(prefix="id") -> str:
    return f"{prefix}-{str(uuid.uuid4().hex)}"
