"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""


class JxException(Exception):
    """
    Base class for all Jx exceptions.
    """


class MissingRequiredArgument(JxException):
    """
    Raised when a component is used/invoked without passing one or more
    of its required arguments (those without a default value).
    """

    def __init__(self, component: str, arg: str) -> None:
        msg = f"`{component}` component requires a `{arg}` argument"
        super().__init__(msg)


class TemplateSyntaxError(JxException):
    """
    Raised when the template syntax is invalid.
    This is usually caused by a missing or extra closing tag.
    """
