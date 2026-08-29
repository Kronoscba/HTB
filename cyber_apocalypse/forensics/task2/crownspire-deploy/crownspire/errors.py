"""Exception hierarchy for crownspire-deploy.

Everything the package raises deliberately inherits from :class:`CrownspireError`
so callers (and the CLI) can catch one type and still print something useful.
"""


class CrownspireError(Exception):
    """Base class for all errors raised by this package."""


class ConfigError(CrownspireError):
    """Raised when required configuration is missing or malformed."""


class ManifestError(CrownspireError):
    """Raised when a sigil manifest fails to load or validate."""


class SigningError(CrownspireError):
    """Raised when signing or signature verification fails."""


class ReliquaryError(CrownspireError):
    """Raised when a reliquary (object store) operation fails."""
