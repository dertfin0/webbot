class WebBotError(Exception):
    pass

class TokenValidationError(WebBotError):
    """
    Raised when bot initialized if given token is invalid
    """
    pass

class VersionError(WebBotError):
    """
    Raised when bot initialized if there is critical difference in version
    """
    pass

class InitRequestError(WebBotError):
    """
    Raised when bot initialized if there are connection issues
    """
    pass