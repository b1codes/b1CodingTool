from typing import List, Optional

class B1Error(Exception):
    """Base exception for all b1CodingTool errors with helpful suggestions."""
    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.suggestions = suggestions or []

class NetworkError(B1Error):
    """Raised when a network operation (like git fetch/clone) fails."""
    pass

class ValidationError(B1Error):
    """Raised when module configuration validation fails."""
    pass

class ProjectError(B1Error):
    """Raised when there's an issue with the project structure (e.g. missing .agents)."""
    pass

class DriftError(B1Error):
    """Raised when a generated file was hand-edited since b1 last wrote it."""
    def __init__(self, files):
        self.files = files
        names = ", ".join(str(f) for f in files)
        super().__init__(
            f"Hand-edited generated files detected: {names}",
            suggestions=["Run `b1 reconcile` to promote or discard the changes."],
        )
