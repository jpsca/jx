"""
Jx | Copyright (c) Juan-Pablo Scaletti <juanpablo@jpscaletti.com>
"""

class JxException(Exception):
    """Base class for all Jx exceptions."""


class TemplateSyntaxError(JxException):
    """
    Raised when the template syntax is invalid.
    This is usually caused by a missing or extra closing tag.
    """


class ImportError(JxException):
    """
    Raised when an import fails.
    This is usually caused by a missing or inaccessible component.
    """
    def __init__(self, relpath: str, **kw) -> None:
        msg = f"Component not found: {relpath}"
        super().__init__(msg, **kw)


class MissingRequiredArgument(JxException):
    """
    Raised when a component is used/invoked without passing one or more
    of its required arguments (those without a default value).
    """

    def __init__(self, component: str, arg: str, **kw) -> None:
        msg = f"{component} component requires a `{arg}` argument"
        super().__init__(msg, **kw)


class DuplicateDefDeclaration(JxException):
    """
    Raised when a component has more then one `{#def ... #}` declarations.
    """

    def __init__(self, component: str, **kw) -> None:
        msg = f"{component} has two `{{#def ... #}}` declarations"
        super().__init__(msg, **kw)


class InvalidArgument(JxException):
    """
    Raised when the arguments passed to the component cannot be parsed
    because of an invalid syntax.
    """


class InvalidImport(JxException):
    """
    Raised when the import cannot be parsed
    """
