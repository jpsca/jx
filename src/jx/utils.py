"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""
import logging
import uuid


logger = logging.getLogger("jx")


def get_random_id(prefix: str = "id") -> str:
    return f"{prefix}-{str(uuid.uuid4().hex)}"
