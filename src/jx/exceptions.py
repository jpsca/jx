"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""

class TemplateSyntaxError(Exception):
    """
    Raised when the template syntax is invalid.
    This is usually caused by a missing or extra closing tag.
    """
