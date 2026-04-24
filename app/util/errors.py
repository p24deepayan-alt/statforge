"""Custom exception hierarchy for StatForge."""


class StatForgeError(Exception):
    """Base exception for all StatForge errors."""


class DataImportError(StatForgeError):
    """Raised when data import fails (bad format, encoding, etc.)."""


class AnalysisError(StatForgeError):
    """Raised when an analysis operation fails."""


class PersistenceError(StatForgeError):
    """Raised when a storage read/write fails."""


class PreprocessingError(StatForgeError):
    """Raised when a preprocessing step is invalid or fails."""
