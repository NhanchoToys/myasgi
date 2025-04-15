class AppError(Exception):
    pass


class LifespanError(AppError):
    pass


class ConnectionClosed(AppError):
    pass


class ParseError(AppError):
    pass
