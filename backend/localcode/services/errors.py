class ServiceError(Exception):
    """An expected, user-facing failure (bad input, unknown id). Mapped to an HTTP status by the API layer."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def not_found(what: str) -> ServiceError:
    return ServiceError(404, f"Unknown {what}")


def bad_request(message: str) -> ServiceError:
    return ServiceError(400, message)
