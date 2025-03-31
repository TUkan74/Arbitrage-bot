from enum import Enum

class HttpMethod(Enum):
    """Enum for HTTP methods used in API requests."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH" 