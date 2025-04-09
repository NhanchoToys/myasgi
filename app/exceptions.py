class AppError(Exception):
    pass


class ConnectionClosed(AppError):
    pass


class ParseError(AppError):
    pass
