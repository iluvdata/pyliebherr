"""Exceptions for the Liebherr API."""


class LiebherrException(Exception):
    """Exception raised for errors in the Liebherr API."""

    def __init__(self, message) -> None:
        """Initialize the exception."""
        self.message = message

    def __str__(self):
        """Return the exception message."""
        return self.message


class LiebherrAuthException(LiebherrException):
    """Exception raised for authentication errors in the Liebherr API."""

    def __init__(self) -> None:
        """Initialize the exception."""
        super().__init__("Invalid API Key")


class LiebherrUpdateException(LiebherrException):
    """Exception raised for update methodes in the Liebherr API."""


class LiebherrFetchException(LiebherrException):
    """Exception raised for fetching data in the Liebherr API."""

    def __init__(self, api_error: str | dict[str, str]) -> None:
        """Initialize the exception."""
        if isinstance(api_error, str):
            super().__init__(api_error)
            return
        super().__init__(
            f"Code: {api_error.get('status', 'Unknown status')}\n{api_error.get('message', 'An error has occured')}\n{api_error.get('error', 'Unknown error')}"
        )


class LiebherrAPILimitExceededException(LiebherrFetchException):
    """Exception raised for HTTP 429 errors."""
